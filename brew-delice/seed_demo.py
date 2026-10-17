"""OPTIONAL: fills the dashboard with clearly-flagged DEMO rows (is_demo=1) so charts look populated.
These are synthetic test data - NOT real customers or sales. Remove with:  python seed_demo.py --clear
Usage:  python seed_demo.py [--clear]"""
import random
import sys
from datetime import datetime, timedelta
from chatbot import analytics

analytics.init_db()
if "--clear" in sys.argv:
    with analytics.get_db() as c:
        for t in ("sessions", "messages", "events", "enquiries", "feedback"):
            c.execute(f"DELETE FROM {t} WHERE is_demo=1")
    print("Demo rows removed."); sys.exit()

random.seed(7)
items = ["coffee", "burger", "fries", "pizza"]
weights = [5, 3, 2, 4]
intents = ["greeting", "menu", "price", "coffee", "pizza", "order", "location", "timings", "recommendation", "thanks"]
with analytics.get_db() as c:
    for n in range(40):
        sid = f"demo{n:04d}x"
        ts = (datetime.now() - timedelta(days=random.randint(0, 6), minutes=random.randint(0, 600))).isoformat(sep=" ", timespec="seconds")
        c.execute("INSERT OR IGNORE INTO sessions VALUES (?,?,1)", (sid, ts))
        for _ in range(random.randint(2, 6)):
            c.execute("INSERT INTO messages(session_id,ts,role,text,intent,confidence,is_demo) VALUES (?,?,?,?,?,?,1)", (sid, ts, "user", "[demo]", random.choice(intents), 0.9))
        c.execute("INSERT INTO events(session_id,ts,event_type,source,is_demo) VALUES (?,?,?,?,1)", (sid, ts, "menu_view", "chat"))
        it = random.choices(items, weights)[0]
        c.execute("INSERT INTO events(session_id,ts,event_type,item,source,is_demo) VALUES (?,?,?,?,?,1)", (sid, ts, "item_selected", it, "chat"))
        if random.random() < .6:
            c.execute("INSERT INTO events(session_id,ts,event_type,item,source,is_demo) VALUES (?,?,?,?,?,1)", (sid, ts, "item_view", it, "chat"))
        if random.random() < .45:
            c.execute("INSERT INTO events(session_id,ts,event_type,item,source,is_demo) VALUES (?,?,?,?,?,1)", (sid, ts, "order_click", it, "chat"))
        if random.random() < .15:
            c.execute("INSERT INTO enquiries(session_id,ts,name,contact,message,item,source,is_demo) VALUES (?,?,?,?,?,?,?,1)",
                      (sid, ts, f"Demo User {n}", "0000000000", "[demo enquiry]", it, "chat"))
            c.execute("INSERT INTO events(session_id,ts,event_type,item,source,is_demo) VALUES (?,?,?,?,?,1)", (sid, ts, "enquiry", it, "chat"))
print("Seeded 40 DEMO conversations (flagged is_demo=1). Use the dashboard scope selector to hide them.")
