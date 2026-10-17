"""Generates the six report diagrams (PNG) with matplotlib. Run: python documentation/make_diagrams.py"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT = os.path.join(os.path.dirname(__file__), "diagrams"); os.makedirs(OUT, exist_ok=True)
ESP, COF, CAR, CRE, BEI, CHA = "#24160f", "#6b4630", "#b8571f", "#fbf4e6", "#ecdcc2", "#1e1a17"
STYLE = {"main": (CRE, COF), "dark": (ESP, ESP), "acc": (CAR, CAR), "soft": (BEI, COF), "ext": ("#ffffff", "#a8977f")}


def canvas(w, h, title):
    fig, ax = plt.subplots(figsize=(w, h)); ax.set_xlim(0, w); ax.set_ylim(0, h); ax.axis("off"); fig.patch.set_facecolor("white")
    ax.text(w / 2, h - 0.3, title, ha="center", va="center", fontsize=15, fontweight="bold", color=ESP, family="serif")
    return fig, ax


def box(ax, x, y, w, h, text, kind="main", fs=9.5, bold=False):
    fc, ec = STYLE[kind]; tc = "white" if kind in ("dark", "acc") else CHA
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fc, ec=ec, lw=1.6))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=fs, color=tc, fontweight="bold" if bold else "normal", linespacing=1.35)
    return (x, y, w, h)


def arrow(ax, a, b, label=None, rad=0.0, fs=8):
    ax.add_patch(FancyArrowPatch(a, b, arrowstyle="-|>", mutation_scale=14, lw=1.6, color=CAR, connectionstyle=f"arc3,rad={rad}"))
    if label: ax.text((a[0] + b[0]) / 2, (a[1] + b[1]) / 2 + 0.12, label, ha="center", fontsize=fs, color=COF, style="italic", bbox=dict(fc="white", ec="none", pad=1))


def group(ax, x, y, w, h, label):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", fc="#fffaf1", ec="#d9c7a8", lw=1.2, ls="--"))
    ax.text(x + 0.15, y + h - 0.25, label, fontsize=9.5, color=CAR, fontweight="bold")


def save(fig, name): fig.savefig(os.path.join(OUT, name), dpi=170, bbox_inches="tight", facecolor="white"); plt.close(fig); print("saved", name)

# 1 architecture
fig, ax = canvas(13, 7, "System Architecture")
group(ax, 0.3, 0.8, 3.2, 5.3, "Browser (client)")
box(ax, 0.6, 4.6, 2.6, 0.9, "Website\nHTML5 · CSS3 · JavaScript", "soft"); box(ax, 0.6, 3.3, 2.6, 0.9, "Chat widget\nchatbot.js", "soft"); box(ax, 0.6, 2.0, 2.6, 0.9, "Admin dashboard\nChart.js / canvas", "soft")
group(ax, 4.2, 0.8, 4.6, 5.3, "Flask server (app.py)")
box(ax, 4.5, 4.8, 4.0, 0.85, "REST API\n/api/chat · /track · /enquiry · /analytics", "dark", 8.3)
box(ax, 4.5, 3.8, 1.9, 0.8, "intent_classifier\n(TF-IDF + cosine)", "main", 8.5); box(ax, 6.6, 3.8, 1.9, 0.8, "nlp_engine\nnormalise · entities", "main", 8.5)
box(ax, 4.5, 2.7, 1.9, 0.8, "response_engine\nrules + replies", "acc", 8.5); box(ax, 6.6, 2.7, 1.9, 0.8, "context_manager\ncurrent item · flow", "main", 8.5)
box(ax, 4.5, 1.1, 4.0, 1.1, "analytics.py\nevent logging · KPIs · enquiries (parameterised SQL)", "main", 8.5)
group(ax, 9.5, 3.2, 3.2, 2.9, "Configuration (JSON)")
box(ax, 9.8, 4.3, 2.6, 0.5, "menu.json · business.json", "soft", 8.5); box(ax, 9.8, 3.6, 2.6, 0.5, "platforms.json · intents.json", "soft", 8.5)
box(ax, 9.8, 1.6, 2.6, 1.0, "SQLite\nchatbot.db", "dark", 10, True)
box(ax, 9.8, 0.25, 2.6, 0.9, "Google Maps · verified\nordering platforms (links)", "ext", 8.5)
arrow(ax, (3.5, 3.75), (4.2, 3.75), "JSON"); arrow(ax, (3.5, 5.0), (4.5, 5.2)); arrow(ax, (6.5, 4.9), (5.4, 4.6)); arrow(ax, (5.45, 3.8), (5.45, 3.5)); arrow(ax, (6.4, 4.2), (6.6, 4.2))
arrow(ax, (6.5, 2.7), (6.5, 2.2)); arrow(ax, (8.5, 1.65), (9.8, 2.0)); arrow(ax, (9.8, 4.0), (8.5, 3.2), "read"); arrow(ax, (3.5, 2.4), (4.5, 1.7), "metrics")
save(fig, "01_system_architecture.png")

# 2 conversation flow
fig, ax = canvas(13, 6.5, "Chatbot Conversation Flow")
y = 4.3
box(ax, 0.3, y, 1.5, 0.9, "Customer:\n“Hi”", "soft"); box(ax, 2.2, y, 2.0, 0.9, "Greeting +\nHow can I help you?", "main")
box(ax, 4.7, y, 1.5, 0.9, "[View Menu]", "acc", 9, True); box(ax, 6.7, y, 2.2, 0.9, "Main Attractions\nCoffee 40 · Burger 59\nFries 59 · Pizza 99", "main")
box(ax, 9.4, y, 1.6, 0.9, "Tap an item\n(e.g. Coffee)", "soft"); box(ax, 11.3, y, 1.5, 0.9, "Item card\n₹ price", "main")
for a, b in [(1.8, 2.2), (4.2, 4.7), (6.2, 6.7), (8.9, 9.4), (11.0, 11.3)]: arrow(ax, (a, y + .45), (b, y + .45))
box(ax, 9.4, 2.6, 1.6, 0.8, "[View Details]", "acc", 9, True); box(ax, 11.3, 2.6, 1.5, 0.8, "[Order Now]", "acc", 9, True)
arrow(ax, (11.9, y), (11.9, 3.4)); arrow(ax, (11.9, y), (10.2, 3.4), rad=0.2)
box(ax, 10.6, 1.0, 2.2, 1.1, "Verified platform?\nYes → platform links\nNo → Contact + Maps", "dark", 8.5); arrow(ax, (12.05, 2.6), (11.9, 2.1))
box(ax, 6.7, 2.6, 2.2, 0.8, "Details + Add to Enquiry", "main", 8.5); arrow(ax, (9.4, 3.0), (8.9, 3.0))
box(ax, 0.3, 2.6, 2.4, 0.8, "“Where are you?” →\nAddress + Get Directions", "main", 8.5); box(ax, 3.1, 2.6, 2.6, 0.8, "“I want to enquire” →\nName → Contact → Message", "main", 8.5)
box(ax, 0.3, 1.0, 2.4, 0.9, "Typed question →\nNLP intent → reply", "soft", 8.5); box(ax, 3.1, 1.0, 2.6, 0.9, "Unknown → Fallback\n+ help buttons", "main", 8.5); box(ax, 6.0, 1.0, 2.9, 0.9, "“Was this helpful?” Yes/No\nNo → “What were you looking for?”", "main", 8.5)
arrow(ax, (3.9, 4.3), (1.5, 3.4), rad=-0.1); arrow(ax, (4.2, 4.3), (4.4, 3.4)); arrow(ax, (4.4, 2.6), (4.4, 1.9), None); arrow(ax, (1.5, 2.6), (1.5, 1.9))
save(fig, "02_conversation_flow.png")

# 3 NLP flow
fig, ax = canvas(13, 4.8, "NLP Method — TF-IDF + Cosine Similarity")
xs = [0.3, 2.65, 5.0, 7.35, 9.7]; labels = ["User message\n“how much is pizza”", "Normalise\nlower-case · strip\npunctuation · ₹→rs", "Vectorise\nTF-IDF char 2–4-grams\n+ word 1–2-grams", "Cosine similarity\nvs. training examples\n(intents.json)", "Best intent\nscore ≥ 0.34?\nelse → fallback"]
kinds = ["soft", "main", "main", "main", "acc"]
for x, l, k in zip(xs, labels, kinds): box(ax, x, 2.6, 2.1, 1.3, l, k, 9)
for i in range(4): arrow(ax, (xs[i] + 2.1, 3.25), (xs[i + 1], 3.25))
box(ax, 2.65, 0.6, 2.1, 1.2, "Entity extraction\nmenu items (exact +\nfuzzy: “burgur”)", "main", 9); box(ax, 5.0, 0.6, 2.1, 1.2, "Context rules\ncurrent item · price/\norder keywords", "main", 9); box(ax, 7.35, 0.6, 2.1, 1.2, "Response engine\nstructured JSON reply\n+ quick-reply buttons", "dark", 9); box(ax, 9.7, 0.6, 2.1, 1.2, "Chat widget\nrenders cards,\nbuttons, links", "soft", 9)
arrow(ax, (3.7, 2.6), (3.7, 1.8)); arrow(ax, (10.75, 2.6), (8.4, 1.8), rad=0.15); arrow(ax, (4.75, 1.2), (5.0, 1.2)); arrow(ax, (7.1, 1.2), (7.35, 1.2)); arrow(ax, (9.45, 1.2), (9.7, 1.2))
save(fig, "03_nlp_flow.png")

# 4 ordering flow
fig, ax = canvas(12, 5.6, "Ordering Flow (verified platforms only)")
box(ax, 0.3, 2.5, 1.9, 1.0, "Customer taps\n“Order Now”", "soft"); box(ax, 2.8, 2.5, 2.1, 1.0, "Log event\norder_click (+item)", "main"); box(ax, 5.5, 2.5, 2.4, 1.0, "platforms.json:\navailable = true\nAND https URL?", "dark")
box(ax, 8.6, 3.9, 3.0, 1.0, "YES → show only verified\nplatform buttons\n(Zomato / Swiggy / Toing)", "acc"); box(ax, 8.6, 0.9, 3.0, 1.1, "NO → “Online ordering platform\ncould not be verified.”\n[Contact Café] [Open Google Maps]", "main", 8.5)
arrow(ax, (2.2, 3.0), (2.8, 3.0)); arrow(ax, (4.9, 3.0), (5.5, 3.0)); arrow(ax, (7.9, 3.3), (8.6, 4.3), "yes"); arrow(ax, (7.9, 2.7), (8.6, 1.6), "no")
box(ax, 8.6, 2.5, 3.0, 0.9, "Click → new tab\nlog platform_selected", "soft", 9); arrow(ax, (10.1, 3.9), (10.1, 3.4))
box(ax, 0.3, 0.6, 7.2, 1.0, "No guessing: a platform is never shown unless the exact Brew Delice Café listing URL is configured.", "ext", 9)
save(fig, "04_ordering_flow.png")

# 5 ER
fig, ax = canvas(13, 6.5, "Database ER Diagram (SQLite)")
def table(x, y, name, cols, w=2.9):
    h = 0.75 + 0.34 * len(cols)
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.1", fc="white", ec=COF, lw=1.6))
    ax.add_patch(FancyBboxPatch((x, y + h - 0.45), w, 0.45, boxstyle="round,pad=0.02,rounding_size=0.1", fc=ESP, ec=ESP))
    ax.text(x + w / 2, y + h - 0.22, name, ha="center", va="center", color="white", fontweight="bold", fontsize=10.5)
    for i, c in enumerate(cols): ax.text(x + 0.15, y + h - 0.7 - 0.34 * i, c, fontsize=8.6, va="center", family="monospace", color=CAR if c.startswith("PK") or c.startswith("FK") else CHA)
    return (x, y, w, h)
table(5.1, 3.6, "sessions", ["PK session_id TEXT", "started_at TEXT", "is_demo INTEGER"])
table(0.3, 0.4, "messages", ["PK id INTEGER", "FK session_id", "ts, role, text", "intent, confidence", "is_demo"])
table(3.6, 0.4, "events", ["PK id INTEGER", "FK session_id", "ts, event_type", "item, platform, intent", "source, is_demo"])
table(6.9, 0.4, "enquiries", ["PK id INTEGER", "FK session_id", "ts, name, contact", "message, item, source", "status, is_demo"])
table(10.2, 0.4, "feedback", ["PK id INTEGER", "FK session_id", "ts, helpful (0/1)", "detail, is_demo"], 2.6)
for x in (1.75, 5.05, 8.35, 11.5): arrow(ax, (x, 2.6 if x < 11 else 2.2), (6.55 if x < 6 else 7.0 if x < 9 else 8.0, 3.6), "1 : N" if x == 1.75 else None, 0.0)
save(fig, "05_database_er_diagram.png")

# 6 analytics flow
fig, ax = canvas(13, 4.6, "Analytics Flow")
xs = [0.3, 2.7, 5.1, 7.5, 9.9]
data = [("User actions\nmenu · item · order\nenquiry · feedback", "soft"), ("log_event() /\nlog_message()\nparameterised SQL", "main"), ("SQLite tables\nsessions · messages\nevents · enquiries", "dark"), ("summary()\nKPIs · rates ·\nchart series", "main"), ("/dashboard\nKPI cards · 5 charts\nenquiries table", "acc")]
for x, (t, k) in zip(xs, data): box(ax, x, 2.2, 2.2, 1.4, t, k, 9)
for i in range(4): arrow(ax, (xs[i] + 2.2, 2.9), (xs[i + 1], 2.9))
box(ax, 0.3, 0.4, 5.9, 1.0, "Enquiry Conversion Rate = chat conversations with an enquiry ÷ conversations × 100", "ext", 9)
box(ax, 6.6, 0.4, 5.5, 1.0, "Order CTR = “Order Now” clicks on an item ÷ items selected × 100", "ext", 9)
save(fig, "06_analytics_flow.png")
