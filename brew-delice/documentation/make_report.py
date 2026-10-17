"""Builds Brew_Delice_Cafe_Chatbot_Report.pdf (reportlab). Run: python documentation/make_report.py"""
import json, os, sys, sqlite3
from datetime import date
from PIL import Image as PILImage
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Image, Table, TableStyle,
                                PageBreak, KeepTogether, ListFlowable, ListItem, NextPageTemplate)

HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE)
SHOT, DIAG = os.path.join(HERE, "screenshots"), os.path.join(HERE, "diagrams")
OUT = os.path.join(ROOT, "documentation", "Brew_Delice_Cafe_Chatbot_Report.pdf")
FD = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("Sans", FD + "DejaVuSans.ttf")); pdfmetrics.registerFont(TTFont("Sans-B", FD + "DejaVuSans-Bold.ttf"))
pdfmetrics.registerFont(TTFont("Sans-I", FD + "DejaVuSans-Oblique.ttf")); pdfmetrics.registerFont(TTFont("Serif-B", FD + "DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFontFamily("Sans", normal="Sans", bold="Sans-B", italic="Sans-I", boldItalic="Sans-B")
ESP, COF, CAR, CRE, BEI = [colors.HexColor(c) for c in ("#24160f", "#6b4630", "#b8571f", "#fbf4e6", "#ecdcc2")]

S = {
 "body": ParagraphStyle("body", fontName="Sans", fontSize=9.6, leading=14.6, alignment=TA_JUSTIFY, spaceAfter=6, textColor=colors.HexColor("#1e1a17")),
 "h1": ParagraphStyle("h1", fontName="Serif-B", fontSize=16, leading=20, textColor=ESP, spaceBefore=10, spaceAfter=8, keepWithNext=1),
 "h2": ParagraphStyle("h2", fontName="Sans-B", fontSize=11, leading=15, textColor=CAR, spaceBefore=6, spaceAfter=4),
 "cap": ParagraphStyle("cap", fontName="Sans-I", fontSize=8.2, leading=11, alignment=TA_CENTER, textColor=COF, spaceAfter=10),
 "cell": ParagraphStyle("cell", fontName="Sans", fontSize=7.6, leading=9.8),
 "cellb": ParagraphStyle("cellb", fontName="Sans-B", fontSize=7.6, leading=9.8, textColor=colors.white),
 "small": ParagraphStyle("small", fontName="Sans-I", fontSize=8, leading=11, textColor=COF),
}
story = []
sec = [0]
def H(t): sec[0] += 1; story.append(Paragraph(f"{sec[0]}. {t}", S["h1"]))
def H2(t): story.append(Paragraph(t, S["h2"]))
def P(t): story.append(Paragraph(t, S["body"]))
def B(items): story.append(ListFlowable([ListItem(Paragraph(i, S["body"]), leftIndent=12) for i in items], bulletType="bullet", bulletFontSize=7, leftIndent=14, bulletColor=CAR))
def sized_img(p, wcm):
    w, h = PILImage.open(p).size; return Image(p, width=wcm * cm, height=wcm * cm * h / w)
def IMG(path, width_cm, cap=None, keep=True):
    w, h = PILImage.open(path).size; W = width_cm * cm
    parts = [Image(path, width=W, height=W * h / w)]
    if cap: parts.append(Paragraph(cap, S["cap"]))
    story.append(KeepTogether(parts) if keep else parts[0])
    if not keep and cap: story.append(Paragraph(cap, S["cap"]))
def TBL(rows, widths, header=True, zebra=True):
    data = [[Paragraph(str(c), S["cellb"] if (header and i == 0) else S["cell"]) for c in r] for i, r in enumerate(rows)]
    t = Table(data, colWidths=[w * cm for w in widths], repeatRows=1 if header else 0)
    st = [("GRID", (0, 0), (-1, -1), .4, colors.HexColor("#d9c7a8")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header: st.append(("BACKGROUND", (0, 0), (-1, 0), ESP))
    if zebra: st += [("BACKGROUND", (0, i), (-1, i), CRE) for i in range(2, len(rows), 2)]
    t.setStyle(TableStyle(st)); story.append(t); story.append(Spacer(1, 8))

# ---------- data from the project ----------
menu = json.load(open(os.path.join(ROOT, "data", "menu.json"), encoding="utf-8"))["items"]
tests = json.load(open(os.path.join(HERE, "test_results.json"), encoding="utf-8"))
passed = sum(t["status"] == "PASS" for t in tests)
con = sqlite3.connect(os.path.join(ROOT, "database", "chatbot.db")); con.row_factory = sqlite3.Row
sys.path.insert(0, ROOT)
os.environ.setdefault("BREW_DB_PATH", os.path.join(ROOT, "database", "chatbot.db"))
from chatbot import analytics
K = analytics.summary(True)["kpis"]

def cover(c, d):
    c.saveState(); c.setFillColor(ESP); c.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    c.setFillColor(CAR); c.rect(0, A4[1] - 1.2 * cm, A4[0], 1.2 * cm, fill=1, stroke=0)
    c.setFillColor(BEI); c.setFont("Sans-B", 9); c.drawString(2 * cm, A4[1] - 0.75 * cm, "DIGITAL MARKETING (MDM) CAPSTONE PROJECT")
    c.restoreState()
def pagenum(c, d):
    c.saveState(); c.setFont("Sans", 8); c.setFillColor(COF)
    c.drawString(2 * cm, 1.1 * cm, "Brew Delice Café – AI Chatbot Automation System"); c.drawRightString(A4[0] - 2 * cm, 1.1 * cm, f"Page {d.page}")
    c.setStrokeColor(BEI); c.line(2 * cm, 1.6 * cm, A4[0] - 2 * cm, 1.6 * cm); c.restoreState()
doc = BaseDocTemplate(OUT, pagesize=A4, leftMargin=2 * cm, rightMargin=2 * cm, topMargin=2 * cm, bottomMargin=2.2 * cm,
                      title="Brew Delice Café – AI Chatbot Automation System", author="Pushkar Singh, Sushant Vairalkar, Kedar Malbhage")
fr = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height, id="f")
doc.addPageTemplates([PageTemplate(id="cover", frames=[Frame(2.2 * cm, 2 * cm, A4[0] - 4.4 * cm, A4[1] - 4.4 * cm)], onPage=cover),
                      PageTemplate(id="body", frames=[fr], onPage=pagenum)])

# ---------- 1 cover ----------
W = lambda t, size, font="Sans", col="white", lead=None, sa=6: Paragraph(t, ParagraphStyle("x", fontName=font, fontSize=size, leading=lead or size * 1.3, textColor=colors.HexColor(col) if isinstance(col, str) else col, spaceAfter=sa))
story += [Spacer(1, 1.6 * cm), Image(os.path.join(ROOT, "static", "images", "profile.png") if os.path.exists(os.path.join(ROOT, "static", "images", "profile.png")) else os.path.join(HERE, "cover_logo.png"), width=3.6 * cm, height=3.6 * cm),
          Spacer(1, 1 * cm), W("BREW DELICE CAFÉ", 30, "Serif-B", "#ffffff", 36), W("AI Chatbot Automation System", 20, "Serif-B", "#d98a3d", 26, 14),
          W("Design and Development of an AI-Driven Multi-Platform Digital Marketing Strategy with Chatbot Automation for Startup Growth", 12, "Sans", "#ecdcc2", 17, 28)]
cov = [["Business", "Brew Delice Café, Pradhikaran, Nigdi, Pimpri-Chinchwad, Maharashtra – 411044"], ["Owner", "Tanmay Koli"],
       ["College", "Pimpri Chinchwad College of Engineering, Pune"], ["Course", "Digital Marketing (MDM) Capstone Project"], ["Guide", "Ms. Shalu Mahajan"],
       ["Team", "Pushkar Singh · Sushant Vairalkar · Kedar Malbhage"], ["Date", date.today().strftime("%d %B %Y")]]
t = Table([[Paragraph(f'<font color="#d98a3d"><b>{a}</b></font>', ParagraphStyle("c", fontName="Sans", fontSize=10, textColor=colors.white)), Paragraph(b, ParagraphStyle("c2", fontName="Sans", fontSize=10, leading=14, textColor=colors.white))] for a, b in cov], colWidths=[3 * cm, 12.5 * cm])
t.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), .4, colors.HexColor("#4a3223")), ("TOPPADDING", (0, 0), (-1, -1), 6), ("BOTTOMPADDING", (0, 0), (-1, -1), 6), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
story += [t, Spacer(1, 1.2 * cm), W("Prototype report — figures shown are prototype/test data, not real customer or sales results.", 8.5, "Sans-I", "#a8977f"),
          NextPageTemplate("body"), PageBreak()]

# ---------- 2.. sections ----------
H("Abstract")
P("This report presents <b>Brew Delice Café – AI Chatbot Automation System</b>, a premium responsive website and a locally-run AI chatbot built for a neighbourhood café in Pradhikaran, Nigdi, Pimpri-Chinchwad. The system lets customers explore the menu, see the Main Attractions (Coffee ₹40, Burger ₹59, French Fries ₹59, Pizza ₹99), view item details, find the café on Google Maps, reach the café's ordering channel and submit enquiries. A TF-IDF and cosine-similarity natural-language engine (Python, Flask, scikit-learn) understands free-text questions, remembers the current item, and every interaction is stored in SQLite and visualised on an analytics dashboard with an Enquiry Conversion Rate and an Order Click-Through Rate. The prototype demonstrates how automation supports the digital-marketing funnel Content → Reach → Engagement → Enquiries for a startup, without paid APIs or cloud accounts.")
H("Introduction")
P("Small cafés compete for attention on Google, social media and food-delivery apps. Customers usually ask the same questions — what is on the menu, how much does it cost, where is the café, how can I order. Answering these manually is slow and is impossible outside working hours. Chatbots automate the repetitive part of customer communication, while analytics reveal what customers are interested in. This project integrates both into a single website designed as part of an <i>AI-Driven Multi-Platform Digital Marketing Strategy</i>.")
H("Business Background")
P("<b>Brew Delice Café</b> is a local café located at Pradhikaran, Nigdi, Pimpri-Chinchwad, Maharashtra – 411044, owned by <b>Tanmay Koli</b>. The café is positioned as a customer-oriented neighbourhood spot offering coffee and quick food at student-friendly prices. The team supplied the Main Attractions and prices used in this project. No business history, awards, reviews, follower counts or sales figures are claimed in this report because none were provided or verified.")
TBL([["Item", "Category", "Price (team-provided)"]] + [[i["name"], i["category"], f'₹{i["price"]}'] for i in menu], [6, 5, 5])
H("Problem Statement")
P("Startup cafés typically lack (a) an always-available channel that answers routine customer questions, (b) a single branded web presence connecting the menu, location and ordering options, and (c) measurable data about customer interest. Without these, potential customers are lost between discovering the café and placing an order or enquiry, and the owner cannot tell which items or channels generate interest.")
H("Aim")
P("To design and develop an AI-driven website and chatbot that improves customer engagement, product discovery and ordering intent for Brew Delice Café, and to measure the impact of each interaction through analytics.")
H("Objectives")
B(["Build a premium, mobile-first café website that clearly represents the Brew Delice Café brand.", "Present the Main Attractions with exact team-provided prices and detailed item views.",
   "Implement a chatbot that follows the required flow (Hi → Menu → Item → Order Now) and also understands natural language.",
   "Link “Order Now” only to ordering platforms where the exact café listing is verified; otherwise offer Contact and Google Maps.",
   "Capture customer enquiries and feedback in an SQLite database.", "Provide an analytics dashboard with KPIs, charts, Enquiry Conversion Rate and Order CTR.", "Run entirely locally with no paid services."])
H("Target Audience")
B(["Students and young professionals around Pradhikaran, Nigdi and Akurdi seeking affordable coffee and snacks.", "Families and groups looking for a quick meal or a place to meet.",
   "Customers who search on Google or delivery apps and want quick answers before visiting or ordering.", "The café owner, who needs enquiries and interest data (admin user)."])
H("Customer Needs")
TBL([["Customer need", "How the system responds"], ["See what is available and the price", "Main Attractions cards, full menu, chatbot menu and price intents"],
     ["Find the café quickly", "Find Us section, Google Maps embed, Get Directions button, “where are you?” intent"], ["Order easily", "Order Now flow routing to verified platform, or Contact Café / Google Maps"],
     ["Ask questions any time", "24×7 chatbot with natural-language understanding and enquiry capture"], ["Trust", "No invented claims; unverified details are clearly marked as such"]], [6, 10])
H("Proposed Solution")
P("A Flask web application serves the website and a JSON chat API. The chatbot combines a TF-IDF/cosine-similarity intent classifier with rule-based entity extraction and a context manager. Menu data, business information and ordering links live in editable JSON files, so the café can update prices or paste a verified ordering link without touching code. All events are written to SQLite and summarised on an admin dashboard. The solution is positioned inside the marketing funnel: <b>Content → Reach → Engagement → Enquiries</b>, where the chatbot drives <i>Customer Engagement → Customer Communication → Product Discovery → Ordering Intent → Enquiry / Order Click</i>.")
H("Website Design")
P("The design combines a warm café aesthetic with a modern SaaS/AI product feel: coffee-brown, cream, beige, charcoal and a single caramel accent colour; a serif display typeface (Fraunces, with Georgia fallback) with Inter for body text; rounded cards, soft shadows, skeleton image loading, scroll-reveal animations and a sticky navigation bar with a mobile menu. Sections: Hero (“Good Coffee. Great Food. Better Moments.”), marketing-funnel strip, Main Attractions, Full Menu with category tabs, About, Find Us (map, address, enquiry form) and footer with project credits. Animations respect <i>prefers-reduced-motion</i>.")
IMG(os.path.join(SHOT, "01_home.png"), 15.5, "Figure 1 – Home page (desktop).")
H("Chatbot Architecture")
P("The browser widget (chatbot.js) sends each message or button action to <b>POST /api/chat</b>. The server pipeline is: validate session → context lookup → intent classification → entity extraction → handler selection → structured JSON reply (text, menu, item card, platform links, location, enquiry summary, quick-reply buttons). The widget renders replies using <i>textContent</i> only, preventing script injection. Modules: <i>nlp_engine.py</i>, <i>intent_classifier.py</i>, <i>response_engine.py</i>, <i>context_manager.py</i>, <i>analytics.py</i>.")
IMG(os.path.join(DIAG, "01_system_architecture.png"), 16, "Figure 2 – System architecture.")
H("Chatbot Conversation Flow")
P("The faculty-required flow is implemented exactly: <b>Hi</b> → “Hello! Welcome to Brew Delice Café.” + “How can I help you?” with [View Menu] [Main Attractions] [Order Online] [Find Us] [Ask a Question]; <b>View Menu</b> → Main Attractions list with prices (each item clickable); <b>Coffee</b> → item card ₹40 with [View Details] [Order Now]; <b>Order Now</b> → verified ordering platforms only. The same paths work through typed natural language.")
IMG(os.path.join(DIAG, "02_conversation_flow.png"), 16.5, "Figure 3 – Conversation flow.")
H("NLP Method")
P("<b>Normalisation</b> lower-cases text, strips punctuation and converts ₹ to “rs”. <b>Vectorisation</b> builds two TF-IDF representations over the training phrases in intents.json — character n-grams (2–4) for tolerance to typos such as “burgur” and word uni/bi-grams for meaning. <b>Classification</b> computes cosine similarity between the user message and each training phrase; an intent’s score is the best similarity, and scores below 0.34 map to <i>fallback</i>. <b>Entity extraction</b> finds menu items (exact and fuzzy). <b>Context rules</b> use the remembered item for follow-ups (“How much?”, “How do I order it?”). The model covers 20 intents: greeting, menu, main_attractions, coffee, burger, fries, pizza, price, location, timings, order, zomato, swiggy, toing, recommendation, enquiry, feedback, thanks, goodbye, fallback.")
IMG(os.path.join(DIAG, "03_nlp_flow.png"), 16.5, "Figure 4 – NLP processing pipeline.")
H("Menu System")
P("menu.json stores each item’s name, price, category, description, image, availability, keywords and ordering links. The website renders Main Attractions cards, a categorised menu board and a detail modal from this file; the chatbot reads the same data, so prices stay consistent everywhere. The file reloads automatically when edited. Only the four team-provided items are included — no additional items were invented.")
IMG(os.path.join(SHOT, "02_main_attractions.png"), 15.5, "Figure 5 – Main Attractions (illustrative food images are replaceable placeholders).")
IMG(os.path.join(SHOT, "03_full_menu.png"), 15.5, "Figure 6 – Full menu with category tabs.")
H("Ordering Platform Integration")
P("<b>Verification.</b> The café owner supplied the café’s own Swiggy page (“Brew Delice Cafe | Nigdi, Pune”): <i>https://www.swiggy.com/menu/1376195?source=sharing</i>. It is configured as the single verified ordering platform. Zomato and Toing were intentionally left out at the owner’s request; since no verified listing exists for them, the chatbot answers honestly (“I couldn’t verify a listing”) and shows no link for them.")
P("<b>Behaviour.</b> platforms.json holds the single source of ordering links. A platform is displayed only when <i>available = true</i> and a https URL is present. Currently only Swiggy qualifies, so “Order Now” (for any orderable item) shows an <b>Order on Swiggy</b> button that opens the café’s real Swiggy page in a new tab and records <i>order_click</i>, <i>item_selected</i> and <i>platform_selected</i> events. If a platform is later removed, the bot falls back to Contact Café and Open Google Maps. A helper script (set_platform.py) validates and sets listing URLs in one command. This behaviour is covered by automated tests T15–T17, T30 and T40.")
IMG(os.path.join(DIAG, "04_ordering_flow.png"), 15.5, "Figure 7 – Ordering flow.")
IMG(os.path.join(SHOT, "07e_chat_card_item_order.png"), 9, "Figure 8 – Ordering an item from the menu card in the chatbot: Order on Swiggy opens the café’s real Swiggy page.")
H("Google Maps Integration")
P("The Find Us section embeds a Google Maps view and provides <b>Get Directions</b> and <b>View on Google</b> buttons. Because the exact Google Business listing URL could not be verified, the buttons currently open a Google Maps <i>search</i> for “Brew Delice Café Pradhikaran Nigdi Pimpri-Chinchwad 411044”; a note on the page and in the chatbot says so. Replacing google_maps_url in business.json with the café’s share link completes the integration. Opening hours and phone number are shown only when verified (currently not displayed).")
IMG(os.path.join(SHOT, "08_find_us.png"), 15.5, "Figure 9 – Find Us section (map preview needs internet; shown here as the offline fallback).")
H("Enquiry System")
P("Typing “I want to enquire” (or tapping Enquiry / Contact Café / Add to Enquiry) starts a three-step flow — Name, Contact, Message — with server-side validation (name letters only; phone 7–15 digits or valid email; message 3–500 characters), cancel support and a confirmation: “Thank you! Your enquiry has been recorded.” The website Find Us form uses the same validation. Data is stored with parameterised SQL and displayed on the dashboard with a status dropdown (New / Contacted / Closed).")
IMG(os.path.join(SHOT, "09_enquiry_form.png"), 15.5, "Figure 10 – Website enquiry form (filled during demo).")
IMG(os.path.join(SHOT, "09b_chat_enquiry_done.png"), 15.5, "Figure 11 – Chatbot enquiry recorded.")
H("Analytics")
P("Every interaction is logged: conversations, messages, menu views, Main-Attraction clicks, item selections and views, order clicks, platform/maps clicks, enquiries, fallbacks and feedback. The dashboard presents six KPI cards, five charts (most selected items, order clicks by item, chatbot intents, enquiries over time, channel clicks) and two derived rates. <b>Enquiry Conversion Rate</b> = chat conversations that ended in an enquiry ÷ all conversations × 100. <b>Order Click-Through Rate</b> = Order Now clicks on an item ÷ items selected × 100. A banner states that all numbers are prototype/test data. Customer feedback (“Was this helpful?”) is stored, and a “No” answer asks “What information were you looking for?”.")
IMG(os.path.join(DIAG, "06_analytics_flow.png"), 16, "Figure 12 – Analytics flow.")
IMG(os.path.join(SHOT, "10_dashboard.png"), 13.5, "Figure 13 – Admin dashboard (prototype test data generated during the demo run).", keep=False)
H("Database Design")
TBL([["Table", "Purpose", "Key columns"], ["sessions", "One row per chatbot conversation", "session_id (PK), started_at, is_demo"], ["messages", "User and bot messages with detected intent", "id, session_id, ts, role, text, intent, confidence"],
     ["events", "Analytics events", "event_type, item, platform, intent, source"], ["enquiries", "Customer enquiries", "name, contact, message, item, source, status"], ["feedback", "Helpful yes/no and follow-up text", "helpful, detail"]], [3, 6.5, 6.5])
IMG(os.path.join(DIAG, "05_database_er_diagram.png"), 16, "Figure 14 – Database ER diagram.")
H("UI Screenshots")
P("Screenshots below were captured automatically from the running application in a real browser (Chromium) following the live-demo sequence.")
IMG(os.path.join(SHOT, "02b_item_detail_modal.png"), 14.5, "Item detail modal (Pizza ₹99) with Order Now and Add to Enquiry.")
os.makedirs(os.path.join(SHOT, "crops"), exist_ok=True)
chat_shots = [("04_chatbot_greeting.png", "Chatbot opening: profile image, welcome, quick actions"), ("04b_chat_hi_response.png", "Typing “Hi”: greeting + View Menu"),
              ("05_chatbot_menu.png", "Menu: Coffee ₹40, Burger ₹59, Fries ₹59, Pizza ₹99"), ("06_coffee_details.png", "Coffee selected: ₹40, View Details, Order Now"),
              ("06b_chat_item_details.png", "Item details with Order Now / Add to Enquiry"), ("07_order_platform_selection.png", "Order Now → Order on Swiggy"),
              ("07b_chat_location.png", "“Where are you located?” → address + directions"), ("07d_chat_category.png", "“show mojito” → category menu"), ("07e_chat_card_item_order.png", "Order Now → Order on Swiggy"), ("07c_chat_natural_language.png", "Natural language: prices, recommendation, Swiggy, thanks"),
              ("09b_chat_enquiry_done.png", "Enquiry recorded in SQLite")]
cells = []
for f, c in chat_shots:
    im = PILImage.open(os.path.join(SHOT, f)).crop((990, 190, 1430, 890)); cp = os.path.join(SHOT, "crops", f); im.save(cp)
    cells.append([sized_img(cp, 5.1), Paragraph(c, S["cap"])])
for i in range(0, len(cells), 3):
    row = cells[i:i + 3]
    while len(row) < 3: row.append(["", ""])
    tt = Table([[r[0] for r in row], [r[1] for r in row]], colWidths=[5.6 * cm] * 3); tt.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP")]))
    story.append(KeepTogether([tt]))
m1, m2 = os.path.join(SHOT, "11_mobile_home.png"), os.path.join(SHOT, "12_mobile_chat.png")
def sized(p, wcm): w, h = PILImage.open(p).size; return Image(p, width=wcm * cm, height=wcm * cm * h / w)
mt = Table([[sized(m1, 6.2), sized(m2, 6.2)], [Paragraph("Mobile home page", S["cap"]), Paragraph("Mobile chatbot (near full-screen)", S["cap"])]], colWidths=[8 * cm, 8 * cm])
story.append(KeepTogether([mt]))
H("Test Cases")
P(f"{len(tests)} automated test cases were executed with <i>python tests/test_chatbot.py</i> against a temporary database. Result: <b>{passed} / {len(tests)} passed</b>.")
TBL([["ID", "Input", "Expected Result", "Actual Result", "Status"]] + [[t["id"], t["input"], t["expected"], t["actual"][:150], t["status"]] for t in tests], [1.0, 3.3, 4.7, 5.9, 1.1])
H("Results / Prototype Observations")
P("The table below is a snapshot of the analytics database after the scripted demo run. <b>These are prototype/test interactions created by the project team while testing; they are not real customers, orders or sales and must not be read as business results.</b>")
TBL([["Metric (prototype/test data)", "Value"], ["Conversations", K["conversations"]], ["User messages", K["messages"]], ["Menu views", K["menu_views"]], ["Items selected", K["item_selected"]], ["Item views", K["item_views"]],
     ["Order clicks", K["order_clicks"]], ["Channel clicks (maps/platform)", K["platform_clicks"]], ["Enquiries", K["enquiries"]], ["Fallback replies", K["fallbacks"]], ["Most requested item", (K["most_popular_item"] or "-").title()],
     ["Enquiry Conversion Rate", f'{K["enquiry_conversion_rate"]}%'], ["Order Click-Through Rate", f'{K["order_ctr"]}%']], [8, 4])
B([f"All {len(tests)} test cases pass, including typo tolerance (“burgur price”), context follow-ups and rejection of unsafe input.", "Typed and button-driven flows produce identical results because both use the same response engine.",
   "The chatbot never displays a platform link, opening hours or phone number that has not been verified.", "Replies are instant on a local machine; no external API is needed."])
H("Limitations")
B(["Only Swiggy is linked (supplied by the owner). Zomato/Toing were left out and have no verified listing; they can be added later with set_platform.py. Prices on the menu card may differ from Swiggy’s listed prices.",
   "The Google Maps button opens a search, not the verified business listing; opening hours and contact number are unverified and not shown.", "Food images are illustrative placeholders, not photographs of the café’s real items; the profile image is a placeholder until the real image is supplied.",
   "The NLP model is small and trained on a limited set of phrases; unusual wording may fall back. English only.", "Analytics shown are test data; real KPIs require real visitors. Chat context is held in memory and resets when the server restarts.",
   "Ordering happens on an external platform, so completed orders cannot be tracked by this system — only order clicks."])
H("Future Scope")
P("The following are <b>not implemented</b> in the current prototype and are listed as realistic extensions:")
B(["WhatsApp Business integration", "Instagram DM integration", "Real-time menu availability", "Online table booking", "Customer segmentation", "Personalised offers", "Sentiment analysis of feedback", "Multilingual chatbot (Hindi / Marathi)", "Voice chatbot", "CRM integration", "Real-time marketing analytics"])
H("Conclusion")
P("The project delivers a complete, locally-runnable website and AI chatbot for Brew Delice Café that supports the full customer journey from discovery to enquiry and measures it. It follows the faculty’s required flow, uses the team-provided prices exactly, applies lightweight NLP without paid APIs, and is deliberately honest about what could and could not be verified. With the café’s real ordering link, Google listing link, opening hours and photographs added to the configuration files, the same system can be used by the café as a practical digital-marketing asset.")
H("References")
B(["Pedregosa, F. et al. (2011). Scikit-learn: Machine Learning in Python. <i>Journal of Machine Learning Research</i>, 12, 2825–2830.",
   "Salton, G. &amp; Buckley, C. (1988). Term-weighting approaches in automatic text retrieval. <i>Information Processing &amp; Management</i>, 24(5), 513–523.",
   "Manning, C. D., Raghavan, P. &amp; Schütze, H. (2008). <i>Introduction to Information Retrieval</i>. Cambridge University Press.",
   "Flask documentation – https://flask.palletsprojects.com", "scikit-learn documentation (TfidfVectorizer, cosine_similarity) – https://scikit-learn.org",
   "SQLite documentation – https://www.sqlite.org/docs.html", "Chart.js documentation – https://www.chartjs.org/docs", "Google Maps URLs documentation – https://developers.google.com/maps/documentation/urls",
   "Café’s Swiggy listing supplied by the owner (17 October 2026) and the café’s printed menu card."])
doc.build(story)
print("PDF written:", OUT)
