"""Turns (intent + entities + context) into structured chatbot replies.

Every reply is a dict:
  {intent, confidence, item, messages:[...], buttons:[...], ask_feedback}
Message types: text | menu | item_card | platforms | no_platform | location | hours | summary
Button: {label, action, payload?}  or  {label, url, track:{platform,item}}
"""
import json
import os
import re
from config import DATA_DIR, MAX_MESSAGE_LEN
from . import analytics
from .nlp_engine import EntityExtractor, has_any, normalize, PRICE_WORDS, ORDER_WORDS, DETAIL_WORDS

ITEM_INTENTS = {"coffee", "burger", "fries", "pizza"}
KEEP_WITH_ITEMS = {"location", "timings", "recommendation", "thanks", "goodbye", "enquiry",
                   "feedback", "zomato", "swiggy", "toing", "greeting"}
INFORMATIVE = {"menu", "main_attractions", "price", "location", "timings", "order", "recommendation",
               "zomato", "swiggy", "toing", "details", "coffee", "burger", "fries", "pizza"}
CANCEL_WORDS = {"cancel", "stop", "exit", "quit", "never mind", "nevermind", "back"}
_CTRL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_EMAIL = re.compile(r"^[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}$")
_NAME = re.compile(r"^[A-Za-zऀ-ॿ][A-Za-zऀ-ॿ .'\-]{1,59}$")


def clean_text(s, limit=MAX_MESSAGE_LEN):
    s = _CTRL.sub("", str(s or "")).strip()
    return re.sub(r"[ \t]+", " ", s)[:limit]


def validate_enquiry(name, contact, message):
    """Server-side validation shared by the chatbot flow and the web form."""
    errors, out = {}, {}
    name = clean_text(name, 80)
    if not name:
        errors["name"] = "Please enter your name."
    elif not _NAME.match(name):
        errors["name"] = "Please enter a valid name (letters only, 2-60 characters)."
    out["name"] = name
    contact = clean_text(contact, 100)
    digits = re.sub(r"[\s\-()+]", "", contact)
    if not contact:
        errors["contact"] = "Please enter a phone number or email."
    elif not (_EMAIL.match(contact) or (digits.isdigit() and 7 <= len(digits) <= 15)):
        errors["contact"] = "Please enter a valid phone number (7-15 digits) or email address."
    out["contact"] = contact
    message = clean_text(message, 500)
    if not message:
        errors["message"] = "Please type your message."
    elif len(message) < 3:
        errors["message"] = "Your message is too short."
    out["message"] = message
    return out, errors


class DataStore:
    """Loads the JSON config files and reloads them automatically when edited."""
    FILES = {"menu": "menu.json", "business": "business.json", "platforms": "platforms.json"}

    def __init__(self):
        self._cache, self._mtimes = {}, {}

    def get(self, key):
        path = os.path.join(DATA_DIR, self.FILES[key])
        m = os.path.getmtime(path)
        if self._mtimes.get(key) != m:
            with open(path, encoding="utf-8") as f:
                self._cache[key] = json.load(f)
            self._mtimes[key] = m
        return self._cache[key]

    def items(self):
        return [i for i in self.get("menu")["items"] if i.get("available", True)]

    def categories(self):
        m = self.get("menu")
        return m.get("categories", [])

    def category_items(self, cat):
        return [i for i in self.items() if i.get("category") == cat]

    def category_emoji(self, cat):
        return self.get("menu").get("category_emoji", {}).get(cat, "🍽")

    def item(self, iid):
        return next((i for i in self.items() if i["id"] == iid), None)

    def verified_platforms(self):
        """Only platforms explicitly marked available WITH an https URL are ever shown."""
        out = []
        for key, p in self.get("platforms")["platforms"].items():
            if p.get("available") and str(p.get("url", "")).startswith("https://"):
                out.append({"key": key, "label": p.get("label", key.title()), "url": p["url"],
                            "text": "Order on " + p.get("label", key.title()), "search": False})
        return out

    def search_platforms(self, only=None):
        """Fallback (NOT verified listings): search links so the customer can still reach Zomato/Swiggy directly."""
        verified = {v["key"] for v in self.verified_platforms()}
        out = []
        for key, p in self.get("platforms")["platforms"].items():
            if key in verified or not str(p.get("search_url", "")).startswith("https://") or (only and key != only):
                continue
            label = p.get("label", key.title())
            out.append({"key": key, "label": label, "url": p["search_url"], "text": "Find on " + label, "search": True})
        return out

    def platform_label(self, key):
        return self.get("platforms")["platforms"].get(key, {}).get("label", key.title())


class ResponseEngine:
    def __init__(self, store, classifier, contexts):
        self.store, self.clf, self.ctxs = store, classifier, contexts
        self.extractor = EntityExtractor(store.get("menu")["items"], store.get("menu").get("category_keywords"))

    # ---------- helpers ----------
    @staticmethod
    def _t(text):
        return {"type": "text", "text": text}

    @staticmethod
    def _btn(label, action, payload=None):
        b = {"label": label, "action": action}
        if payload:
            b["payload"] = payload
        return b

    def _payload(self, it):
        return {"id": it["id"], "name": it["name"], "emoji": it.get("emoji", ""), "price": it["price"],
                "category": it.get("category"), "description": it.get("description", ""),
                "main": bool(it.get("main_attraction")), "orderable": it.get("orderable", True),
                "image": "/static/" + it.get("image", ""), "currency": self.store.get("menu").get("currency", "₹")}

    def _price_text(self, it):
        return f'{it["name"]} is {self.store.get("menu").get("currency", "₹")}{it["price"]}.'

    def _maps(self):
        b = self.store.get("business")
        return b["google_maps_url"], b.get("google_business_url")

    def _contact_buttons(self):
        maps, _ = self._maps()
        return [self._btn("📩 Contact Café", "enquiry_start"),
                {"label": "📍 Open Google Maps", "url": maps, "track": {"platform": "google_maps"}}]

    def _main_buttons(self):
        return [self._btn("🍽 View Menu", "menu"), self._btn("🛵 Order Online", "order"),
                self._btn("📍 Find Us", "location"), self._btn("💬 Enquiry", "enquiry_start")]

    def _reply(self, intent, conf, item, messages, buttons=None, feedback=False):
        return {"intent": intent, "confidence": conf, "item": item, "messages": messages,
                "buttons": buttons or [], "ask_feedback": feedback}

    # ---------- public entry ----------
    def handle(self, sid, text=None, action=None, payload=None, label=None, demo=0):
        analytics.ensure_session(sid, demo)
        ctx = self.ctxs.get(sid)
        if action:
            return self._on_action(sid, ctx, action, payload, label, demo)
        text = clean_text(text)
        if not text:
            return self._reply("empty", 0.0, ctx["item"], [self._t("Please type a message — for example “show menu” or “coffee price”. 😊")],
                               [self._btn("🍽 View Menu", "menu"), self._btn("📍 Find Us", "location")])
        # multi-step flows capture the next message
        if ctx["state"]:
            res = self._flow(sid, ctx, text, demo)
            if res:
                return res
        intent, conf, _ = self.clf.classify(text)
        items, cats = self.extractor.find_entities(text)
        if not items and not cats and has_any(text, ("full menu", "complete menu", "entire menu", "all items", "whole menu")):
            intent = "fullmenu"
        if intent == "fallback" and not items and not cats:
            if has_any(text, PRICE_WORDS):
                intent = "price"
            elif has_any(text, ORDER_WORDS):
                intent = "order"
        if cats and not items and intent not in KEEP_WITH_ITEMS and intent != "fullmenu":
            intent = "category"
        if items and intent not in KEEP_WITH_ITEMS:
            if has_any(text, PRICE_WORDS):
                intent = "price"
            elif has_any(text, ORDER_WORDS):
                intent = "order"
            elif has_any(text, DETAIL_WORDS):
                intent = "details"
            else:
                intent = items[0] if items[0] in ITEM_INTENTS else "item"
        analytics.log_message(sid, "user", text, intent, conf, demo)
        res = self._dispatch(sid, ctx, intent, conf, items, demo, source="chat", cats=cats)
        analytics.log_message(sid, "bot", " / ".join(m.get("text", m["type"]) for m in res["messages"])[:300], res["intent"], None, demo)
        return res

    # ---------- button actions ----------
    def _on_action(self, sid, ctx, action, payload, label, demo):
        if action == "enquiry_start":
            ctx["state"], ctx["data"] = None, {}
        intent_map = {"menu": "menu", "attractions": "main_attractions", "prices": "price", "location": "location",
                      "timings": "timings", "order": "order", "enquiry_start": "enquiry", "recommend": "recommendation",
                      "ask": "ask", "greeting": "greeting", "feedback_start": "feedback", "fullmenu": "fullmenu"}
        items, cats = [], []
        if action.startswith("cat:"):
            cat = action.split(":", 1)[1]
            if cat not in self.store.categories():
                return self._reply("fallback", 0.0, None, [self._t("Sorry, I couldn't find that menu section.")], self._main_buttons())
            cats, intent = [cat], "category"
            analytics.log_message(sid, "user", label or action, intent, 1.0, demo)
            self.ctxs.reset_flow(sid)
            res = self._dispatch(sid, ctx, intent, 1.0, [], demo, source="chat", cats=cats)
            analytics.log_message(sid, "bot", " / ".join(m.get("text", m["type"]) for m in res["messages"])[:300], res["intent"], None, demo)
            return res
        if action.startswith(("item:", "details:", "order:")):
            kind, iid = action.split(":", 1)
            if not self.store.item(iid):
                return self._reply("fallback", 0.0, None, [self._t("Sorry, that item isn't available right now.")], self._main_buttons())
            items, intent = [iid], {"item": iid, "details": "details", "order": "order"}[kind]
            if kind == "item":
                intent = iid if iid in ITEM_INTENTS else "item"
        elif action in ("feedback_yes", "feedback_no"):
            analytics.log_message(sid, "user", label or action, "feedback", 1.0, demo)
            return self._feedback(sid, ctx, action == "feedback_yes", demo)
        elif action == "cancel":
            self.ctxs.reset_flow(sid)
            return self._reply("cancel", 1.0, ctx["item"], [self._t("No problem — cancelled. What would you like to do next?")], self._main_buttons())
        elif action in intent_map:
            intent = intent_map[action]
            if action in ("order", "enquiry_start") and isinstance(payload, str) and self.store.item(payload):
                items = [payload]
        else:
            return self._reply("fallback", 0.0, None, [self._t("Sorry, I didn't understand that action.")], self._main_buttons())
        if action != "enquiry_start":
            self.ctxs.reset_flow(sid)
        analytics.log_message(sid, "user", label or action, intent, 1.0, demo)
        res = self._dispatch(sid, ctx, intent, 1.0, items, demo, source="chat")
        analytics.log_message(sid, "bot", " / ".join(m.get("text", m["type"]) for m in res["messages"])[:300], res["intent"], None, demo)
        return res

    # ---------- intent handlers ----------
    def _dispatch(self, sid, ctx, intent, conf, items, demo, source, cats=None):
        ctx["turns"] += 1
        ctx["last_intent"] = intent
        biz = self.store.get("business")
        name = biz["business_name"]
        cur = self.store.get("menu").get("currency", "₹")
        all_items = self.store.items()
        by_id = {i["id"]: i for i in all_items}
        sel = [by_id[i] for i in items if i in by_id]
        log = lambda et, **kw: analytics.log_event(sid, et, intent=intent, source=source, demo=demo, **kw)

        # periodic feedback prompt after a few helpful answers (and always after thanks / bye)
        feedback = intent in INFORMATIVE and ctx["turns"] >= 3 and (ctx["turns"] - 3) % 4 == 0
        feedback = feedback or intent in ("thanks", "goodbye")
        R = lambda msgs, btns=None, item=None: self._reply(intent, conf, item if item is not None else ctx["item"], msgs, btns, feedback)

        if intent == "greeting":
            return R([self._t(f"Hello! 👋 Welcome to {name}."), self._t("How can I help you?")],
                     [self._btn("🍽 View Menu", "menu"), self._btn("⭐ Main Attractions", "attractions"),
                      self._btn("🛵 Order Online", "order"), self._btn("📍 Find Us", "location"),
                      self._btn("❓ Ask a Question", "ask")])

        if intent in ("menu", "main_attractions"):
            ctx["item"] = None
            log("menu_view" if intent == "menu" else "attraction_click")
            head = "Here's our menu 🍽" if intent == "menu" else "Here are our Main Attractions ⭐"
            tail = " — tap any item to see details, or pick a menu section below." if intent == "menu" else " — tap any item to see details."
            return R([self._t(head + tail),
                      {"type": "menu", "title": "Main Attractions", "items": [self._payload(i) for i in all_items if i.get("main_attraction")]}],
                     self._category_buttons() + [self._btn("📖 Full Menu", "fullmenu"), self._btn("🛵 Order Online", "order"), self._btn("📍 Find Us", "location")], item=None)

        if intent == "fullmenu":
            ctx["item"] = None
            log("menu_view")
            msgs = [self._t("Here is our complete menu 📖 (prices as per the café's menu card). Tap any item for details.")]
            for c in self.store.categories():
                lst = self.store.category_items(c)
                if lst:
                    msgs.append({"type": "menu", "title": f'{self.store.category_emoji(c)} {c}', "items": [self._payload(i) for i in lst]})
            return R(msgs, [self._btn("🛵 Order Online", "order"), self._btn("📍 Find Us", "location")], item=None)

        if intent == "category":
            cat = (cats or [None])[0]
            lst = self.store.category_items(cat) if cat else []
            if not lst:
                return self._unavailable(intent, conf, ctx)
            ctx["item"] = None
            log("menu_view")
            others = [self._btn(f'{self.store.category_emoji(c)} {c}', f"cat:{c}") for c in self.store.categories() if c != cat and self.store.category_items(c)]
            return R([self._t(f'Here\'s our {cat} menu {self.store.category_emoji(cat)} — tap an item for details.'),
                      {"type": "menu", "title": cat, "items": [self._payload(i) for i in lst]}],
                     [self._btn("🛵 Order Online", "order"), self._btn("📖 Full Menu", "fullmenu")] + others[:4], item=None)

        if intent in ITEM_INTENTS or intent == "item" or (intent == "details" and not sel and ctx["item"]):
            it = sel[0] if sel else (by_id.get(ctx["item"] or intent) or by_id.get(intent))
            if not it:
                return self._unavailable(intent, conf, ctx)
            if intent == "details":
                sel = [it]
            else:
                ctx["item"] = it["id"]
                log("item_selected", item=it["id"])
                cards = [self._t(f'{it["emoji"]} {it["name"]} — {cur}{it["price"]}'), {"type": "item_card", "item": self._payload(it)}]
                btns = [self._btn("👁 View Details", f'details:{it["id"]}')]
                if it.get("orderable", True):
                    btns.append(self._btn("🛒 Order Now", f'order:{it["id"]}'))
                return R(cards, btns + [self._btn("🍽 View Menu", "menu")], item=it["id"])

        if intent == "details":
            it = sel[0] if sel else None
            if not it:
                return R([self._t("Which item would you like to know more about?")], self._item_buttons("item"))
            ctx["item"] = it["id"]
            log("item_selected", item=it["id"])
            log("item_view", item=it["id"])
            return R([self._t(f'{it["emoji"]} {it["name"]} — {cur}{it["price"]}'),
                      {"type": "item_card", "item": self._payload(it)},
                      self._t(it.get("long_description") or it.get("description", ""))],
                     ([self._btn("🛒 Order Now", f'order:{it["id"]}')] if it.get("orderable", True) else []) +
                     [self._btn("📝 Add to Enquiry", "enquiry_start", it["id"]), self._btn("🍽 View Menu", "menu")], item=it["id"])

        if intent == "price":
            use = sel or ([by_id[ctx["item"]]] if ctx["item"] in by_id else [])
            if use:
                ctx["item"] = use[0]["id"]
                for it in use:
                    log("item_selected", item=it["id"])
                text = " ".join(self._price_text(i) for i in use)
                ob = [self._btn("🛒 Order Now", f'order:{use[0]["id"]}')] if use[0].get("orderable", True) else []
                return R([self._t(text)] + [{"type": "item_card", "item": self._payload(i)} for i in use[:2]],
                         ob + [self._btn("💰 All Prices", "prices")], item=use[0]["id"])
            return R([self._t("Here are our Main Attractions with prices 💰 — pick a section below for the rest of the menu."),
                      {"type": "menu", "title": "Prices", "items": [self._payload(i) for i in all_items if i.get("main_attraction")]}],
                     self._category_buttons() + [self._btn("📖 Full Menu", "fullmenu"), self._btn("🛵 Order Online", "order")])

        if intent == "order":
            it = sel[0] if sel else by_id.get(ctx["item"])
            if it:
                ctx["item"] = it["id"]
                if sel:
                    log("item_selected", item=it["id"])
            log("order_click", item=it["id"] if it else None)
            return self._order_reply(R, it)

        if intent in ("zomato", "swiggy", "toing"):
            ver = [p for p in self.store.verified_platforms() if p["key"] == intent]
            label = self.store.platform_label(intent)
            it = by_id.get(ctx["item"])
            if ver:
                return R([self._t(f"Yes! {name} is available on {label}. ✅"),
                          {"type": "platforms", "item": it["id"] if it else None, "platforms": ver}])
            srch = self.store.search_platforms(only=intent)
            msgs = [self._t(f"I couldn't verify a {name} listing on {label} yet, so I won't claim a direct link."),
                    self._t(f"Tap below to search for us on {label}, or contact the café / open Google Maps.")] if srch else \
                   [self._t(f"I couldn't verify a {name} listing on {label} yet, so I won't share a link."),
                    self._t("You can contact the café or open our location on Google Maps instead.")]
            if srch:
                msgs.append({"type": "platforms", "item": it["id"] if it else None, "platforms": srch, "search": True})
            return R(msgs, self._contact_buttons() + [self._btn("🍽 View Menu", "menu")])

        if intent == "location":
            maps, google = self._maps()
            a = biz["address"]
            addr = a.get("verified_listing_address") or f'{a["line1"]}, {a["city"]}, {a["state"]} – {a["pincode"]}'
            msgs = [self._t(f"📍 {name} is at {addr}."),
                    {"type": "location", "name": name, "address": addr, "maps_url": maps, "google_url": google}]
            if not biz.get("maps_link_verified"):
                msgs.append(self._t("Note: the map button opens a Google Maps search for the café; the exact listing link is still being confirmed."))
            return R(msgs, [{"label": "🧭 Get Directions", "url": maps, "track": {"platform": "google_maps"}},
                            {"label": "🔎 View on Google", "url": google, "track": {"platform": "google_search"}},
                            self._btn("🕐 Timings", "timings")])

        if intent == "timings":
            hrs = biz.get("opening_hours")
            if hrs:
                return R([self._t("🕐 Opening hours"), {"type": "hours", "hours": hrs}], [self._btn("📍 Find Us", "location")])
            maps, google = self._maps()
            return R([self._t("🕐 Opening hours haven't been verified yet, so I won't guess."),
                      self._t("Please check the café's Google listing, or send an enquiry and the café will get back to you.")],
                     [{"label": "🔎 View on Google", "url": google, "track": {"platform": "google_search"}},
                      self._btn("💬 Enquiry", "enquiry_start")])

        if intent == "recommendation":
            ordered = sorted([i for i in all_items if i.get("main_attraction")], key=lambda i: i["price"])
            cheap, top = ordered[0], ordered[-1]
            txt = (f'I can\'t claim a "bestseller" without real sales data, but here are good starting points: '
                   f'{cheap["emoji"]} {cheap["name"]} ({cur}{cheap["price"]}) is our lowest-priced item, and '
                   f'{top["emoji"]} {top["name"]} ({cur}{top["price"]}) is our highest-priced item. '
                   f'For a combo, {by_id["coffee"]["name"] if "coffee" in by_id else cheap["name"]} + Burger comes to '
                   f'{cur}{(by_id["coffee"]["price"] if "coffee" in by_id else cheap["price"]) + (by_id["burger"]["price"] if "burger" in by_id else 0)}.')
            return R([self._t(txt)], self._item_buttons("item") + [self._btn("🍽 View Menu", "menu")])

        if intent == "enquiry":
            it = sel[0] if sel else by_id.get(ctx["item"])
            ctx["state"], ctx["data"] = "enq_name", {"item": it["id"] if it else None}
            return R([self._t("Sure, I'll note your enquiry. 📝 What's your name?")], [self._btn("✖ Cancel", "cancel")])

        if intent == "feedback":
            return R([self._t("We'd love your feedback! Was this chatbot helpful?")],
                     [self._btn("👍 Yes", "feedback_yes"), self._btn("👎 No", "feedback_no")])

        if intent == "ask":
            return R([self._t("Of course! Ask me about our menu, prices, location, timings or how to order — or leave an enquiry and the café will get back to you.")],
                     [self._btn("💰 Prices", "prices"), self._btn("🕐 Timings", "timings"),
                      self._btn("🛵 Order Online", "order"), self._btn("💬 Enquiry", "enquiry_start")])

        if intent == "thanks":
            return R([self._t("You're welcome! 😊 Anything else I can help with?")],
                     [self._btn("🍽 View Menu", "menu"), self._btn("🛵 Order Online", "order")])

        if intent == "goodbye":
            return R([self._t(f"Goodbye! 👋 Thanks for visiting {name}. See you soon!")])

        # fallback
        log("fallback")
        return self._reply("fallback", conf, ctx["item"],
                           [self._t("Sorry, I didn't quite get that. 🤔 I can help with the menu, prices, location, timings, ordering and enquiries.")],
                           [self._btn("🍽 View Menu", "menu"), self._btn("💰 Prices", "prices"), self._btn("📍 Find Us", "location"),
                            self._btn("🛵 Order Online", "order"), self._btn("💬 Enquiry", "enquiry_start")])

    def _item_buttons(self, kind):
        return [self._btn(f'{i["emoji"]} {i["name"]}', f'{kind}:{i["id"]}') for i in self.store.items() if i.get("main_attraction")]

    def _category_buttons(self):
        skip = {"French Fries", "Pizza"}   # single-item sections already listed under Main Attractions
        return [self._btn(f'{self.store.category_emoji(c)} {c}', f"cat:{c}") for c in self.store.categories()
                if c not in skip and self.store.category_items(c)]

    def _unavailable(self, intent, conf, ctx):
        return self._reply(intent, conf, None, [self._t("Sorry, that item isn't available right now.")], self._main_buttons())

    def _order_reply(self, R, it):
        verified = self.store.verified_platforms()
        if it and not it.get("orderable", True):
            return R([self._t(f'{it["name"]} is an add-on ({self.store.get("menu").get("currency", "₹")}{it["price"]}) — add it when you order a burger or sandwich on the ordering app.')], self._main_buttons())
        cur = self.store.get("menu").get("currency", "₹")
        pick = [] if it else self._item_buttons("order")
        if verified:
            msgs = []
            if it:
                msgs.append(self._t(f'{it["name"]} ({cur}{it["price"]}) is available for online ordering through the verified platform shown below.'
                                    if len(verified) == 1 else
                                    f'{it["name"]} ({cur}{it["price"]}) is available for online ordering through the verified platforms shown below.'))
            msgs += [self._t("Where would you like to order?" if len(verified) > 1 else "Choose your ordering platform:"),
                     {"type": "platforms", "item": it["id"] if it else None, "platforms": verified}]
            return R(msgs, pick)
        maps, _ = self._maps()
        msgs = []
        if it:
            msgs.append(self._t(f'{it["emoji"]} {it["name"]} — {cur}{it["price"]}'))
        msgs += [self._t("Online ordering platform could not be verified."),
                 self._t("I couldn't confirm the exact Brew Delice Café listing, so I won't claim a direct order link. "
                         "Use the Zomato / Swiggy search below to find us, or contact the café / open Google Maps.")]
        srch = self.store.search_platforms()
        if srch:
            msgs.append({"type": "platforms", "item": it["id"] if it else None, "platforms": srch, "search": True})
        msgs.append({"type": "no_platform", "item": it["id"] if it else None})
        return R(msgs, self._contact_buttons() + pick)

    # ---------- multi-step flows ----------
    def _flow(self, sid, ctx, text, demo):
        low = normalize(text)
        state = ctx["state"]
        if low in CANCEL_WORDS:
            self.ctxs.reset_flow(sid)
            return self._reply("cancel", 1.0, ctx["item"], [self._t("No problem — cancelled. What would you like to do next?")], self._main_buttons())
        analytics.log_message(sid, "user", text if state != "enq_contact" else "[contact details]", "enquiry", 1.0, demo)
        cancel = [self._btn("✖ Cancel", "cancel")]
        if state == "fb_detail":
            analytics.update_feedback_detail(ctx["data"].get("fid"), text)
            self.ctxs.reset_flow(sid)
            return self._reply("feedback", 1.0, ctx["item"], [self._t("Thank you — your feedback has been recorded and helps us improve. 🙏")], self._main_buttons())
        if state == "enq_name":
            out, err = validate_enquiry(text, "9999999", "abc")
            if "name" in err:
                return self._reply("enquiry", 1.0, ctx["item"], [self._t(err["name"])], cancel)
            ctx["data"]["name"], ctx["state"] = out["name"], "enq_contact"
            return self._reply("enquiry", 1.0, ctx["item"], [self._t(f'Nice to meet you, {out["name"]}! 😊 What\'s the best phone number or email to reach you on?')], cancel)
        if state == "enq_contact":
            out, err = validate_enquiry("Ab", text, "abc")
            if "contact" in err:
                return self._reply("enquiry", 1.0, ctx["item"], [self._t(err["contact"])], cancel)
            ctx["data"]["contact"], ctx["state"] = out["contact"], "enq_message"
            it = self.store.item(ctx["data"].get("item")) if ctx["data"].get("item") else None
            prompt = f'What would you like to ask about {it["name"]}?' if it else "What would you like to ask or tell us?"
            return self._reply("enquiry", 1.0, ctx["item"], [self._t(prompt)], cancel)
        if state == "enq_message":
            out, err = validate_enquiry("Ab", "9999999", text)
            if "message" in err:
                return self._reply("enquiry", 1.0, ctx["item"], [self._t(err["message"])], cancel)
            d = ctx["data"]
            msg = out["message"]
            it = self.store.item(d.get("item")) if d.get("item") else None
            analytics.add_enquiry(sid, d["name"], d["contact"], msg, item=d.get("item"), source="chat", demo=demo)
            self.ctxs.reset_flow(sid)
            return self._reply("enquiry", 1.0, ctx["item"],
                               [self._t("Thank you! Your enquiry has been recorded. ✅"),
                                {"type": "summary", "rows": [["Name", d["name"]], ["Contact", d["contact"]]] +
                                 ([["Item", it["name"]]] if it else []) + [["Message", msg]]},
                                self._t("The café team will get back to you.")], self._main_buttons())
        return None

    def _feedback(self, sid, ctx, helpful, demo):
        fid = analytics.save_feedback(sid, helpful, demo=demo)
        if helpful:
            return self._reply("feedback", 1.0, ctx["item"], [self._t("Thank you! 😊 Glad I could help.")], self._main_buttons())
        ctx["state"], ctx["data"] = "fb_detail", {"fid": fid}
        return self._reply("feedback", 1.0, ctx["item"], [self._t("Sorry about that. What information were you looking for?")],
                           [self._btn("✖ Skip", "cancel")])
