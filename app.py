"""Brew Delice Café - website + AI chatbot (Flask).  Run:  python app.py"""
import hmac
import os
import re
from functools import wraps
from flask import Flask, jsonify, render_template, request, Response
import config
from chatbot import analytics
from chatbot.context_manager import ContextManager
from chatbot.intent_classifier import IntentClassifier
from chatbot.response_engine import DataStore, ResponseEngine, validate_enquiry

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024
app.json.ensure_ascii = False

store = DataStore()
engine = ResponseEngine(store, IntentClassifier(), ContextManager())
analytics.init_db()
SID_RE = re.compile(r"^[A-Za-z0-9_\-]{8,64}$")


def admin_required(fn):
    @wraps(fn)
    def wrapper(*a, **kw):
        if config.ADMIN_PASSWORD:
            auth = request.authorization
            if not (auth and hmac.compare_digest(auth.username or "", config.ADMIN_USER)
                    and hmac.compare_digest(auth.password or "", config.ADMIN_PASSWORD)):
                return Response("Admin login required", 401, {"WWW-Authenticate": 'Basic realm="Brew Delice Admin"'})
        return fn(*a, **kw)
    return wrapper


def profile_image():
    """Uses static/images/profile.(png|jpg|jpeg|webp) if you drop the real profile photo there."""
    for ext in ("png", "jpg", "jpeg", "webp"):
        if os.path.exists(os.path.join(config.STATIC_DIR, "images", f"profile.{ext}")):
            return f"images/profile.{ext}"
    return store.get("business").get("profile_image", "images/profile.svg")


def client_config():
    biz, menu = store.get("business"), store.get("menu")
    return {
        "business": biz["business_name"], "currency": menu.get("currency", "₹"),
        "profile": "/static/" + profile_image(),
        "maps_url": biz["google_maps_url"], "google_url": biz.get("google_business_url"),
        "platforms": store.verified_platforms(), "search_platforms": store.search_platforms(),
        "items": [engine._payload(i) for i in store.items()],
    }


@app.after_request
def headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "same-origin"
    if request.path.startswith("/api/"):
        resp.headers["Cache-Control"] = "no-store"
    return resp


@app.get("/")
def index():
    biz, menu = store.get("business"), store.get("menu")
    items = store.items()
    groups = [{"name": c, "emoji": store.category_emoji(c), "items": store.category_items(c)} for c in store.categories() if store.category_items(c)]
    return render_template("index.html", biz=biz, menu=menu, items=items, main_items=[i for i in items if i.get("main_attraction")],
                           groups=groups, profile=profile_image(),
                           verified=store.verified_platforms(), cfg=client_config())


@app.get("/dashboard")
@admin_required
def dashboard():
    return render_template("dashboard.html", biz=store.get("business"), profile=profile_image(),
                           notice=config.PROTOTYPE_NOTICE, items={i["id"]: i["name"] for i in store.items()},
                           chart_local=os.path.exists(os.path.join(config.STATIC_DIR, "vendor", "chart.umd.js")))


def _sid(data):
    sid = str((data or {}).get("session_id", ""))
    return sid if SID_RE.match(sid) else None


@app.post("/api/chat")
def api_chat():
    data = request.get_json(silent=True) or {}
    sid = _sid(data)
    if not sid:
        return jsonify(error="invalid session_id"), 400
    action = data.get("action")
    text = data.get("message")
    if action is not None and not isinstance(action, str):
        return jsonify(error="invalid action"), 400
    res = engine.handle(sid, text=text if isinstance(text, str) else None, action=action,
                        payload=data.get("payload"), label=str(data.get("label", ""))[:80] or None,
                        demo=1 if data.get("demo") else 0)
    return jsonify(res)


@app.post("/api/track")
def api_track():
    data = request.get_json(silent=True) or {}
    sid = _sid(data)
    if not sid:
        return jsonify(error="invalid session_id"), 400
    ev = data.get("event")
    item = data.get("item")
    item = item if isinstance(item, str) and store.item(item) else None
    platform = str(data.get("platform") or "")[:30] or None
    ok = analytics.log_event(sid, ev, item=item, platform=platform, intent=None,
                             source=str(data.get("source") or "web")[:10], demo=1 if data.get("demo") else 0) if isinstance(ev, str) else False
    return jsonify(ok=bool(ok)), (200 if ok else 400)


@app.post("/api/enquiry")
def api_enquiry():
    data = request.get_json(silent=True) or {}
    sid = _sid(data) or "web-form-anon"
    out, errors = validate_enquiry(data.get("name"), data.get("contact"), data.get("message"))
    if errors:
        return jsonify(ok=False, errors=errors), 400
    item = data.get("item") if isinstance(data.get("item"), str) and store.item(data.get("item")) else None
    eid = analytics.add_enquiry(sid, out["name"], out["contact"], out["message"], item=item, source="web",
                                demo=1 if data.get("demo") else 0)
    return jsonify(ok=True, id=eid, message="Thank you! Your enquiry has been recorded.")


@app.get("/api/analytics")
@admin_required
def api_analytics():
    inc = request.args.get("include_demo", "1") != "0"
    data = analytics.summary(inc)
    data["notice"] = config.PROTOTYPE_NOTICE
    data["items"] = {i["id"]: i["name"] for i in store.items()}
    return jsonify(data)


@app.get("/api/enquiries")
@admin_required
def api_enquiries():
    return jsonify(analytics.list_enquiries(request.args.get("include_demo", "1") != "0"))


@app.patch("/api/enquiries/<int:eid>")
@admin_required
def api_enquiry_status(eid):
    data = request.get_json(silent=True) or {}
    ok = analytics.set_enquiry_status(eid, data.get("status"))
    return jsonify(ok=ok), (200 if ok else 400)


@app.get("/api/health")
def health():
    return jsonify(status="ok", platforms_verified=len(store.verified_platforms()))


if __name__ == "__main__":
    print(f"\n  Brew Delice Café  ->  http://{config.HOST}:{config.PORT}\n  Dashboard         ->  http://{config.HOST}:{config.PORT}/dashboard\n")
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)
