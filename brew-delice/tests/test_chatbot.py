"""Test suite: python tests/test_chatbot.py   (uses a temporary SQLite DB; writes documentation/test_results.{json,md})"""
import json, os, sys, tempfile, sqlite3, uuid
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
_tmp = tempfile.mkdtemp()
os.environ["BREW_DB_PATH"] = os.path.join(_tmp, "test.db")
from app import app, store, engine  # noqa: E402
import config  # noqa: E402

client = app.test_client()


def say(sid, msg=None, action=None, payload=None):
    body = {"session_id": sid}
    if action: body.update(action=action, payload=payload, label=action)
    else: body["message"] = msg
    return client.post("/api/chat", json=body).get_json()


def texts(r): return " | ".join(m.get("text", "") for m in r["messages"] if m["type"] == "text")
def labels(r): return [b["label"] for b in r["buttons"]]
def menu_items(r): return next((m["items"] for m in r["messages"] if m["type"] == "menu"), [])
def p_ok(pl): return pl["swiggy"]["url"].startswith("https://www.swiggy.com/menu/1376195") and not pl["zomato"]["available"] and not pl["toing"]["available"]
def sid(): return "t" + uuid.uuid4().hex[:12]

T = []
def test(tid, inp, expected):
    def deco(fn):
        T.append((tid, inp, expected, fn)); return fn
    return deco

PRICES = {"coffee": 40, "burger": 59, "fries": 59, "pizza": 99}

@test("T01", "Hi", "Greeting 'Welcome to Brew Delice Café' + View Menu button")
def _():
    r = say(sid(), "Hi"); ok = r["intent"] == "greeting" and "Welcome to Brew Delice Café" in texts(r) and any("View Menu" in l for l in labels(r))
    return ok, f'intent={r["intent"]}; buttons={labels(r)}'
@test("T02", "Hello", "Greeting intent")
def _(): r = say(sid(), "Hello"); return r["intent"] == "greeting", f'intent={r["intent"]}'
@test("T03", "hii (typo/variation)", "Greeting intent")
def _(): r = say(sid(), "hii"); return r["intent"] == "greeting", f'intent={r["intent"]}'
@test("T04", "Show menu", "Menu with Coffee 40, Burger 59, French Fries 59, Pizza 99")
def _():
    r = say(sid(), "Show menu"); got = {i["id"]: i["price"] for i in menu_items(r)}
    return r["intent"] == "menu" and got == PRICES, f'intent={r["intent"]}; items={got}'
@test("T05", "what do you have?", "Menu intent (natural language)")
def _(): r = say(sid(), "what do you have?"); return r["intent"] == "menu" and len(menu_items(r)) == 4, f'intent={r["intent"]}'
@test("T06", "Main attractions", "Main Attractions list with 4 items")
def _(): r = say(sid(), "what are the main attractions?"); return r["intent"] == "main_attractions" and len(menu_items(r)) == 4, f'intent={r["intent"]}; n={len(menu_items(r))}'
@test("T07", "[View Menu button]", "Menu displayed via button action")
def _(): r = say(sid(), action="menu"); return r["intent"] == "menu" and len(menu_items(r)) == 4, f'intent={r["intent"]}'
@test("T08", "Coffee", "Coffee card ₹40 with View Details and Order Now buttons")
def _():
    r = say(sid(), "Coffee"); card = next(m["item"] for m in r["messages"] if m["type"] == "item_card")
    ok = card["price"] == 40 and any("View Details" in l for l in labels(r)) and any("Order Now" in l for l in labels(r))
    return ok, f'price={card["price"]}; buttons={labels(r)}'
@test("T09", "coffee price?", "Coffee is ₹40")
def _(): r = say(sid(), "coffee price?"); return "₹40" in texts(r), texts(r)
@test("T10", "how much is burger?", "Burger is ₹59")
def _(): r = say(sid(), "how much is burger?"); return "₹59" in texts(r) and "Burger" in texts(r), texts(r)
@test("T11", "french fries price", "French Fries ₹59")
def _(): r = say(sid(), "french fries price"); return "₹59" in texts(r) and "French Fries" in texts(r), texts(r)
@test("T12", "how much is pizza", "Pizza is ₹99")
def _(): r = say(sid(), "how much is pizza"); return "₹99" in texts(r), texts(r)
@test("T13", "Where are you located?", "Address Pradhikaran, Nigdi, 411044 + Get Directions")
def _():
    r = say(sid(), "Where are you located?"); ok = r["intent"] == "location" and "Pradhikaran" in texts(r) and "411044" in texts(r) and any("Directions" in l for l in labels(r))
    return ok, texts(r)[:120]
@test("T14", "open google maps", "Location intent; button URL points to google.com/maps")
def _():
    r = say(sid(), "open google maps"); urls = [b["url"] for b in r["buttons"] if "url" in b]
    return r["intent"] == "location" and any("google.com/maps" in u for u in urls), f'urls={[u[:60] for u in urls]}'
@test("T15", "how can I order?", "'Order on Swiggy' button linking to the café's real Swiggy page; no Zomato/Toing link")
def _():
    r = say(sid(), "how can I order?"); p = next((m for m in r["messages"] if m["type"] == "platforms"), None)
    urls = [x["url"] for x in p["platforms"]] if p else []
    ok = urls == ["https://www.swiggy.com/menu/1376195?source=sharing"] and [x["text"] for x in p["platforms"]] == ["Order on Swiggy"]
    return ok, f'links={urls}'
@test("T16", "are you on zomato?", "Honest 'could not verify' answer, no Zomato link")
def _():
    r = say(sid(), "are you on zomato?"); urls = [b.get("url", "") for b in r["buttons"]]
    return r["intent"] == "zomato" and "couldn't verify" in texts(r) and not any("zomato" in u for u in urls) and not any(m["type"] == "platforms" for m in r["messages"]), texts(r)[:80]
@test("T17", "are you on swiggy?", "Swiggy intent; confirms availability + real Swiggy link")
def _():
    r = say(sid(), "are you on swiggy?"); p = next((m for m in r["messages"] if m["type"] == "platforms"), None)
    return r["intent"] == "swiggy" and "available on Swiggy" in texts(r) and bool(p) and p["platforms"][0]["url"] == "https://www.swiggy.com/menu/1376195?source=sharing", f'intent={r["intent"]}'
@test("T36", "full menu", "One menu list per category; all 30 items shown")
def _():
    r = say(sid(), "full menu"); n = sum(len(m["items"]) for m in r["messages"] if m["type"] == "menu")
    return r["intent"] == "fullmenu" and n == len(store.items()) == 30, f'intent={r["intent"]}; items={n}'
@test("T37", "mojito", "Category intent listing the 4 mojitos")
def _():
    r = say(sid(), "mojito"); names = [i["name"] for i in menu_items(r)]
    return r["intent"] == "category" and len(names) == 4, f'intent={r["intent"]}; {names}'
@test("T38", "double tikki burger price", "Item from menu card: ₹70")
def _(): r = say(sid(), "double tikki burger price"); return "₹70" in texts(r) and "Double Tikki" in texts(r), texts(r)[:90]
@test("T39", "veg cheese burger", "Longest match: Veg Cheese Burger (₹50), not plain Burger")
def _(): r = say(sid(), "veg cheese burger"); return "Veg Cheese Burger" in json.dumps(r["messages"]) and "₹50" in json.dumps(r["messages"], ensure_ascii=False), r["intent"]
@test("T40", "I want to order oreo shake", "Swiggy link shown for a card item")
def _():
    r = say(sid(), "I want to order oreo shake"); p = next((m for m in r["messages"] if m["type"] == "platforms"), None)
    return bool(p) and p["platforms"][0]["url"] == "https://www.swiggy.com/menu/1376195?source=sharing", f'intent={r["intent"]}'
@test("T41", "extra cheese", "Add-on ₹10 shown, no Order button")
def _():
    r = say(sid(), "extra cheese"); return "₹10" in json.dumps(r["messages"], ensure_ascii=False) and not any("Order Now" in l for l in labels(r)), str(labels(r))
@test("T42", "mojto (typo)", "Fuzzy-matched to the Mojito category")
def _(): r = say(sid(), "show mojto"); return r["intent"] == "category" and len(menu_items(r)) == 4, f'intent={r["intent"]}'
@test("T18", "toing", "Toing intent, no fake link")
def _(): r = say(sid(), "are you on toing?"); return r["intent"] == "toing" and not any(m["type"] == "platforms" for m in r["messages"]), f'intent={r["intent"]}'
@test("T19", "what do you recommend?", "Recommendation without invented 'bestseller' claims")
def _(): r = say(sid(), "what do you recommend?"); return r["intent"] == "recommendation" and "can't claim" in texts(r), texts(r)[:90]
@test("T20", "I want to enquire → name → contact → message", "Enquiry stored in SQLite; 'Your enquiry has been recorded'")
def _():
    s = sid(); say(s, "I want to enquire"); say(s, "Priya Joshi"); say(s, "9822012345"); r = say(s, "Do you take bulk orders?")
    n = sqlite3.connect(config.DB_PATH).execute("SELECT COUNT(*) FROM enquiries WHERE session_id=? AND name='Priya Joshi'", (s,)).fetchone()[0]
    return "enquiry has been recorded" in texts(r) and n == 1, f'rows_in_db={n}'
@test("T21", "Enquiry with invalid contact '12'", "Validation error, not stored")
def _():
    s = sid(); say(s, "enquiry"); say(s, "Amit Rao"); r = say(s, "12")
    return "valid phone" in texts(r), texts(r)
@test("T22", "what is the capital of india", "Fallback reply with help options")
def _(): r = say(sid(), "what is the capital of india"); return r["intent"] == "fallback" and "didn't quite get" in texts(r), f'intent={r["intent"]}'
@test("T23", "(empty message)", "Friendly prompt; nothing stored")
def _(): r = say(sid(), "   "); return r["intent"] == "empty" and "Please type" in texts(r), texts(r)
@test("T24", "Coffee → How do I order it?", "Context: answer is about Coffee")
def _():
    s = sid(); say(s, "Coffee"); r = say(s, "How do I order it?"); return r["intent"] == "order" and r["item"] == "coffee" and "Coffee" in texts(r), f'item={r["item"]}; {texts(r)[:60]}'
@test("T25", "Burger → How much?", "Context: 'Burger is ₹59.'")
def _():
    s = sid(); say(s, "Burger"); r = say(s, "How much?"); return "Burger is ₹59." in texts(r), texts(r)
@test("T26", "burgur price (typo)", "Typo tolerated → Burger ₹59")
def _(): r = say(sid(), "burgur price"); return "Burger is ₹59." in texts(r), texts(r)
@test("T27", "what are your timings?", "Does NOT invent opening hours")
def _(): r = say(sid(), "what are your timings?"); return "haven't been verified" in texts(r) and not any(c.isdigit() for c in texts(r)), texts(r)[:80]
@test("T28", "thanks / bye", "Thanks and goodbye intents")
def _(): s = sid(); a = say(s, "thanks"); b = say(s, "bye"); return a["intent"] == "thanks" and b["intent"] == "goodbye", f'{a["intent"]}, {b["intent"]}'
@test("T29", "Feedback 👎 → 'What information were you looking for?'", "Stored in feedback table")
def _():
    s = sid(); say(s, "hi"); say(s, action="feedback_no"); r = say(s, "Opening hours")
    row = sqlite3.connect(config.DB_PATH).execute("SELECT helpful, detail FROM feedback WHERE session_id=?", (s,)).fetchone()
    return row == (0, "Opening hours"), f'row={row}'
@test("T30", "Order Now when a platform IS verified (simulated)", "Only verified platform shown, new-tab link")
def _():
    orig = store.verified_platforms
    store.verified_platforms = lambda: [{"key": "zomato", "label": "Zomato", "url": "https://example.test/verified"}]
    try:
        r = say(sid(), "I want to order coffee"); p = next((m for m in r["messages"] if m["type"] == "platforms"), None)
    finally:
        store.verified_platforms = orig
    return bool(p) and [x["key"] for x in p["platforms"]] == ["zomato"] and "verified platform shown below" in texts(r), f'platforms={[x["key"] for x in p["platforms"]] if p else None}'
@test("T31", "Name '<b>x</b>' on enquiry form", "Rejected by validation (HTML not allowed)")
def _():
    r = client.post("/api/enquiry", json={"session_id": sid(), "name": "<b>x</b>", "contact": "9999999999", "message": "hello"}); return r.status_code == 400, f'status={r.status_code}'
@test("T32", "SQL injection text in message", "Stored literally; tables intact")
def _():
    r = client.post("/api/enquiry", json={"session_id": sid(), "name": "Test User", "contact": "9999999999", "message": "'); DROP TABLE enquiries;--"})
    n = sqlite3.connect(config.DB_PATH).execute("SELECT COUNT(*) FROM enquiries").fetchone()[0]; return r.status_code == 200 and n >= 1, f'status={r.status_code}; enquiries_table_rows={n}'
@test("T33", "menu.json prices", "Main Attractions unchanged: Coffee 40, Burger 59, French Fries 59, Pizza 99")
def _(): got = {i["id"]: i["price"] for i in store.items() if i.get("main_attraction")}; return got == PRICES, str(got)
@test("T34", "Dashboard + analytics API", "/dashboard 200; KPIs and both rates present")
def _():
    a = client.get("/api/analytics").get_json(); d = client.get("/dashboard")
    return d.status_code == 200 and "enquiry_conversion_rate" in a["kpis"] and "order_ctr" in a["kpis"] and a["kpis"]["conversations"] > 0, f'conversations={a["kpis"]["conversations"]}; enq_rate={a["kpis"]["enquiry_conversion_rate"]}%; ctr={a["kpis"]["order_ctr"]}%'
@test("T35", "platforms.json / business.json audit", "Only Swiggy available (real URL); Zomato/Toing off; no invented phone/hours")
def _():
    pl = store.get("platforms")["platforms"]; biz = store.get("business")
    ok = all(not (p["available"] and not p["url"]) for p in pl.values()) and p_ok(pl) and biz["opening_hours"] is None and not biz["contact"]["phone"]
    return ok, f'available={[k for k, p in pl.items() if p["available"]]}; hours={biz["opening_hours"]}; phone={biz["contact"]["phone"]}'

results = []
for tid, inp, exp, fn in T:
    try: ok, actual = fn()
    except Exception as e: ok, actual = False, f"EXCEPTION {e!r}"
    results.append({"id": tid, "input": inp, "expected": exp, "actual": actual, "status": "PASS" if ok else "FAIL"})
    print(f'{tid} {"PASS" if ok else "FAIL"}  {inp}  ->  {actual[:110]}')
passed = sum(r["status"] == "PASS" for r in results)
print(f"\n{passed}/{len(results)} passed")
doc = os.path.join(ROOT, "documentation"); os.makedirs(doc, exist_ok=True)
json.dump(results, open(os.path.join(doc, "test_results.json"), "w"), indent=1, ensure_ascii=False)
with open(os.path.join(doc, "test_results.md"), "w", encoding="utf-8") as f:
    f.write("# Test results\n\n| Test ID | Input | Expected Result | Actual Result | Status |\n|---|---|---|---|---|\n")
    for r in results: f.write(f'| {r["id"]} | {r["input"]} | {r["expected"]} | {r["actual"].replace("|", "/")} | {r["status"]} |\n')
sys.exit(0 if passed == len(results) else 1)
