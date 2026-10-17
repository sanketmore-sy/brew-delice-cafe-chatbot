"""SQLite persistence + analytics queries. All queries are parameterised."""
import os
import sqlite3
from datetime import datetime
from config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  session_id TEXT PRIMARY KEY, started_at TEXT NOT NULL, is_demo INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS messages (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT NOT NULL, ts TEXT NOT NULL,
  role TEXT NOT NULL, text TEXT, intent TEXT, confidence REAL, is_demo INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, ts TEXT NOT NULL, event_type TEXT NOT NULL,
  item TEXT, platform TEXT, intent TEXT, source TEXT DEFAULT 'chat', is_demo INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS enquiries (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, ts TEXT NOT NULL, name TEXT NOT NULL,
  contact TEXT NOT NULL, message TEXT NOT NULL, item TEXT, source TEXT DEFAULT 'chat',
  status TEXT NOT NULL DEFAULT 'New', is_demo INTEGER NOT NULL DEFAULT 0);
CREATE TABLE IF NOT EXISTS feedback (
  id INTEGER PRIMARY KEY AUTOINCREMENT, session_id TEXT, ts TEXT NOT NULL, helpful INTEGER NOT NULL,
  detail TEXT, is_demo INTEGER NOT NULL DEFAULT 0);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id);
"""
EVENT_TYPES = {"menu_view", "attraction_click", "item_selected", "item_view", "order_click",
               "platform_selected", "enquiry", "fallback", "feedback", "chat_open"}
STATUSES = ("New", "Contacted", "Closed")


def now():
    return datetime.now().isoformat(sep=" ", timespec="seconds")


def get_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as c:
        c.executescript(SCHEMA)


def ensure_session(sid, demo=0):
    """Returns True when this call created a new conversation."""
    with get_db() as c:
        cur = c.execute("INSERT OR IGNORE INTO sessions(session_id, started_at, is_demo) VALUES (?,?,?)",
                        (sid, now(), demo))
        return cur.rowcount == 1


def log_message(sid, role, text, intent=None, confidence=None, demo=0):
    with get_db() as c:
        c.execute("INSERT INTO messages(session_id, ts, role, text, intent, confidence, is_demo) VALUES (?,?,?,?,?,?,?)",
                  (sid, now(), role, (text or "")[:1000], intent, confidence, demo))


def log_event(sid, event_type, item=None, platform=None, intent=None, source="chat", demo=0):
    if event_type not in EVENT_TYPES:
        return False
    with get_db() as c:
        c.execute("INSERT INTO events(session_id, ts, event_type, item, platform, intent, source, is_demo) VALUES (?,?,?,?,?,?,?,?)",
                  (sid, now(), event_type, item, platform, intent, source, demo))
    return True


def add_enquiry(sid, name, contact, message, item=None, source="chat", demo=0):
    with get_db() as c:
        cur = c.execute("INSERT INTO enquiries(session_id, ts, name, contact, message, item, source, is_demo) VALUES (?,?,?,?,?,?,?,?)",
                        (sid, now(), name, contact, message, item, source, demo))
        eid = cur.lastrowid
    log_event(sid, "enquiry", item=item, source=source, demo=demo)
    return eid


def save_feedback(sid, helpful, detail=None, demo=0):
    with get_db() as c:
        cur = c.execute("INSERT INTO feedback(session_id, ts, helpful, detail, is_demo) VALUES (?,?,?,?,?)",
                        (sid, now(), 1 if helpful else 0, detail, demo))
        fid = cur.lastrowid
    log_event(sid, "feedback", intent="helpful" if helpful else "not_helpful", demo=demo)
    return fid


def update_feedback_detail(fid, detail):
    with get_db() as c:
        c.execute("UPDATE feedback SET detail=? WHERE id=?", ((detail or "")[:500], fid))


def set_enquiry_status(eid, status):
    if status not in STATUSES:
        return False
    with get_db() as c:
        return c.execute("UPDATE enquiries SET status=? WHERE id=?", (status, eid)).rowcount == 1


def list_enquiries(include_demo=True, limit=50):
    q = "SELECT id, ts, name, contact, message, item, source, status, is_demo FROM enquiries"
    if not include_demo:
        q += " WHERE is_demo=0"
    q += " ORDER BY id DESC LIMIT ?"
    with get_db() as c:
        return [dict(r) for r in c.execute(q, (limit,))]


def _count(c, sql, args=()):
    return c.execute(sql, args).fetchone()[0]


def summary(include_demo=True):
    flt = "" if include_demo else " AND is_demo=0"
    w = "" if include_demo else " WHERE is_demo=0"
    with get_db() as c:
        conv = _count(c, "SELECT COUNT(*) FROM sessions" + w)
        msgs = _count(c, "SELECT COUNT(*) FROM messages WHERE role='user'" + flt)
        ev = {r["event_type"]: r["n"] for r in c.execute(
            "SELECT event_type, COUNT(*) n FROM events WHERE 1=1" + flt + " GROUP BY event_type")}
        by_item = lambda et: {r["item"]: r["n"] for r in c.execute(
            "SELECT item, COUNT(*) n FROM events WHERE event_type=? AND item IS NOT NULL" + flt + " GROUP BY item ORDER BY n DESC", (et,))}
        selected, orders = by_item("item_selected"), by_item("order_click")
        platforms = {r["platform"]: r["n"] for r in c.execute(
            "SELECT platform, COUNT(*) n FROM events WHERE event_type='platform_selected' AND platform IS NOT NULL" + flt + " GROUP BY platform ORDER BY n DESC")}
        intents = {r["intent"]: r["n"] for r in c.execute(
            "SELECT intent, COUNT(*) n FROM messages WHERE role='user' AND intent IS NOT NULL" + flt + " GROUP BY intent ORDER BY n DESC")}
        enq_time = {r["d"]: r["n"] for r in c.execute(
            "SELECT substr(ts,1,10) d, COUNT(*) n FROM enquiries WHERE 1=1" + flt + " GROUP BY d ORDER BY d")}
        fb = {r["helpful"]: r["n"] for r in c.execute("SELECT helpful, COUNT(*) n FROM feedback WHERE 1=1" + flt + " GROUP BY helpful")}
        demo_rows = _count(c, "SELECT COUNT(*) FROM events WHERE is_demo=1")
        enquiries = _count(c, "SELECT COUNT(*) FROM enquiries WHERE 1=1" + flt)
        conv_with_enq = _count(c, "SELECT COUNT(DISTINCT e.session_id) FROM enquiries e JOIN sessions s ON s.session_id=e.session_id WHERE e.source='chat'" + flt.replace("is_demo", "e.is_demo"))
        order_item_clicks = _count(c, "SELECT COUNT(*) FROM events WHERE event_type='order_click' AND item IS NOT NULL" + flt)
        feedback_details = [dict(r) for r in c.execute(
            "SELECT ts, detail FROM feedback WHERE helpful=0 AND detail IS NOT NULL" + flt + " ORDER BY id DESC LIMIT 5")]
    sel_total = sum(selected.values())
    top = max(selected, key=selected.get) if selected else None
    return {
        "kpis": {
            "conversations": conv, "messages": msgs, "menu_views": ev.get("menu_view", 0),
            "attraction_clicks": ev.get("attraction_click", 0), "item_views": ev.get("item_view", 0),
            "item_selected": sel_total, "order_clicks": ev.get("order_click", 0),
            "platform_clicks": ev.get("platform_selected", 0), "enquiries": enquiries,
            "fallbacks": ev.get("fallback", 0), "feedback_yes": fb.get(1, 0), "feedback_no": fb.get(0, 0),
            "most_popular_item": top,
            "conversations_with_enquiry": conv_with_enq,
            "enquiry_conversion_rate": round(100 * conv_with_enq / conv, 1) if conv else 0.0,
            "order_ctr": round(min(100.0, 100 * order_item_clicks / sel_total), 1) if sel_total else 0.0,
        },
        "charts": {"items_selected": selected, "order_clicks_by_item": orders, "intents": intents,
                   "enquiries_over_time": enq_time, "platform_clicks": platforms},
        "feedback_details": feedback_details,
        "demo_rows": demo_rows,
    }
