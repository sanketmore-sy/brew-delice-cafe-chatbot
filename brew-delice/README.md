# Brew Delice Café — Website + AI Chatbot

**Digital Marketing (MDM) Capstone · Pimpri Chinchwad College of Engineering, Pune**
*Design and Development of an AI-Driven Multi-Platform Digital Marketing Strategy with Chatbot Automation for Startup Growth*

Business: **Brew Delice Café**, Pradhikaran, Nigdi, Pimpri-Chinchwad, Maharashtra – 411044 · Owner: Tanmay Koli
Guide: Ms. Shalu Mahajan · Team: Pushkar Singh, Sushant Vairalkar, Kedar Malbhage

---

## 1. Project overview
A premium café website with an embedded chatbot that helps customers discover the menu, check prices, find the café, reach the ordering channel and leave enquiries — while measuring every step for the digital-marketing funnel **Content → Reach → Engagement → Enquiries**.
It runs **100 % locally**: no paid APIs, no API keys, no cloud accounts.

## 2. Features
- Premium responsive café website (Home, Main Attractions, Full Menu, About, Find Us, footer, sticky nav, scroll-to-top)
- **Main Attractions** exactly as given by the team: ☕ Coffee ₹40 · 🍔 Burger ₹59 · 🍟 French Fries ₹59 · 🍕 Pizza ₹99 (cards, details modal, Order Now, Add to Enquiry)
- Floating chatbot (full-screen on mobile) with the faculty flow: **Hi → Menu → Item → Order Now → platform**
- Real lightweight NLP: **TF-IDF + cosine similarity** (scikit-learn), 20 intents, typo-tolerant, context-aware ("How do I order it?")
- Enquiry capture (Name → Contact → Message) stored in **SQLite** + website enquiry form
- Feedback widget (👍/👎 → "What information were you looking for?")
- Analytics dashboard at `/dashboard`: KPI cards, 5 charts, Enquiry Conversion Rate, Order CTR, enquiries table with status
- Google Maps "Get Directions" and "View on Google" buttons
- Security: server-side validation, parameterised SQL, XSS-safe rendering (`textContent`), optional admin password

### ⚠️ Honest-data policy (important for evaluation)
- **Ordering platforms:** the café's real **Swiggy** page (supplied by the owner, `https://www.swiggy.com/menu/1376195?source=sharing`) is configured as verified — chatbot **Order Now** and the website show **"Order on Swiggy"**, opening that page in a new tab. **Zomato/Toing were left out** (no verified listing); the bot says so honestly and shows no link.
- **Menu:** 30 items from the café's printed menu card (Burger, Sandwich, Mojito, Coffee & Shakes, Combo & Extras) plus the 4 team-provided Main Attractions (Coffee ₹40, Burger ₹59, French Fries ₹59, Pizza ₹99 — unchanged). Edit `data/menu.json` to change items/prices. Chatbot: "full menu", "mojito", "veg cheese burger", "extra cheese" etc. all work. Menu-card prices may differ from Swiggy prices.
- **Google Maps:** the buttons open a Google Maps *search* for "Brew Delice Café Pradhikaran Nigdi" until you paste the café's real share link (see §11).
- Opening hours, phone, reviews, offers: **not invented** (left empty/unverified).
- Food images are illustrative SVG placeholders; the profile image is a placeholder — replace with real files (§8).
- Dashboard numbers are prototype/test data and are labelled as such.

## 3. Architecture
```
Browser (HTML/CSS/JS)  ──►  Flask app.py  ──►  chatbot/
  index.html, chatbot.js      /api/chat           intent_classifier.py  (TF-IDF + cosine)
  dashboard.html              /api/track          nlp_engine.py         (normalise, entities)
                              /api/enquiry        response_engine.py    (replies, flows)
                              /api/analytics      context_manager.py    (current item, state)
                              /dashboard          analytics.py          (SQLite, KPIs)
data/*.json (menu, business, platforms, intents)  ·  database/chatbot.db (SQLite)
```
Diagrams: `documentation/diagrams/`.

## 4. Technology stack
HTML5 · CSS3 · JavaScript (no framework) · Python 3.10+ · Flask · scikit-learn (TF-IDF, cosine similarity) · SQLite · Chart.js (with offline canvas fallback)

## 5. Installation (Windows)
Open **Command Prompt** in the project folder (`brew-delice`):
```bat
py -m venv venv
venv\Scripts\activate
pip install Flask scikit-learn numpy
python app.py
```
(`pip install -r requirements.txt` also works; it additionally installs reportlab/matplotlib/playwright, which are only needed to regenerate the PDF/screenshots.)

macOS / Linux:
```bash
python3 -m venv venv && source venv/bin/activate
pip install Flask scikit-learn numpy
python app.py
```
Open **http://127.0.0.1:5000** — the dashboard is at **http://127.0.0.1:5000/dashboard**.
Optional admin password: `set BREW_ADMIN_PASSWORD=yourpassword` (Windows) / `export BREW_ADMIN_PASSWORD=yourpassword` (Linux/macOS) before `python app.py` (login user: `admin`).

## 6. Database
SQLite file `database/chatbot.db` is created automatically on first run (tables: `sessions`, `messages`, `events`, `enquiries`, `feedback`). To reset all data: stop the server and delete `database/chatbot.db`.
Optional demo data (flagged `is_demo=1`, hideable on the dashboard): `python seed_demo.py` · remove: `python seed_demo.py --clear`.

## 7. NLP explanation
1. Message is normalised (lower-case, punctuation removed, ₹ → "rs").
2. Two TF-IDF views are built over the training phrases in `data/intents.json`: **character 2–4-grams** (typo tolerance) and **word 1–2-grams**.
3. **Cosine similarity** against every training phrase; an intent's score is its best phrase. Below **0.34** → `fallback`.
4. Entity extraction finds menu items (exact + fuzzy, e.g. "burgur").
5. Context rules combine intent + item + conversation context (`context_manager.py`), e.g. "How much?" after "Burger" → *Burger is ₹59.*
To improve accuracy simply add more example phrases to `data/intents.json` and restart.

## 8. Replacing the profile image / food photos
- Profile / logo: put the café's real image at `static/images/profile.png` (or `.jpg/.webp`) — it is picked up automatically everywhere (navbar, chat, footer, favicon).
- Food photos: replace `static/images/food/*.svg` or change the `image` path of each item in `data/menu.json`.

## 9. Editing the menu
Edit `data/menu.json` (name, price, description, `available`, `image`, `category`, `keywords`). Changes are picked up without restarting. Add new items only after verifying them with the café.

## 10. Editing ordering platforms
Easiest — one command per platform (it validates the link):
```bat
python set_platform.py zomato "https://www.zomato.com/pune/<exact-listing>"
python set_platform.py swiggy "https://www.swiggy.com/restaurants/<exact-listing>"
```
After that, chatbot **Order Now** shows direct **"Order on Zomato / Swiggy"** buttons (new tab) and the search fallback disappears for that platform. Or edit by hand:
`data/platforms.json`:
```json
"zomato": { "label": "Zomato", "available": true, "url": "https://www.zomato.com/pune/<exact-brew-delice-listing>", "verified_on": "2026-10-14" }
```
A platform is shown **only if** `available` is `true` **and** `url` starts with `https://`. Open the listing, confirm it is *Brew Delice Café, Pradhikaran/Nigdi*, then paste its URL.

## 11. Google Maps configuration
`data/business.json` → `google_maps_url` (button link), `google_maps_embed_url` (map preview), `google_business_url` ("View on Google"). To use the exact listing: open the café in Google Maps → Share → Copy link → paste into `google_maps_url`, and set `"maps_link_verified": true`. Fill `opening_hours` (e.g. `{"Mon–Sun": "9:00 AM – 10:00 PM"}`) and `contact.phone` **only** when verified.

## 12. Analytics
Tracked: conversations, messages, menu views, Main-Attraction clicks, item selections/views, order clicks, platform/maps clicks, enquiries, fallbacks, feedback, most requested item.
- **Enquiry Conversion Rate** = chat conversations that ended in an enquiry ÷ all conversations × 100
- **Order Click-Through Rate** = "Order Now" clicks on an item ÷ items selected × 100
Dashboard: `/dashboard` (auto-refresh every 10 s). Chart.js loads from `static/vendor/chart.umd.js` (if you place it there) or the cdnjs CDN; offline, a built-in canvas renderer draws the charts.

## 13. Testing
```bat
python tests/test_chatbot.py
```
35 test cases (greeting, menu, prices, location, ordering, platforms, NLP variations, context, enquiry validation, SQL-injection, empty/unknown input…). Results: `documentation/test_results.md`.
Browser demo + screenshots: `python tests/take_screenshots.py` (needs `playwright install chromium`).

## 14. Live demo script (17 steps)
1 Open site → 2 show landing page → 3 click **Chat with us** → 4 type **Hi** → 5 greeting + menu option → 6 click **View Menu** → 7 Coffee ₹40 · Burger ₹59 · Fries ₹59 · Pizza ₹99 → 8 click **Coffee** → 9 Coffee ₹40 + Order Now → 10 click **Order Now** → 11 verified-platform step (or the honest "could not be verified" + Contact/Maps) → 12 open the ordering page / Google Maps → 13 back to chat → 14 type **Where are you located?** → 15 click **Get Directions** → 16 open `/dashboard` → 17 show enquiry + order-click tracking.

## 15. Future scope (NOT implemented yet)
WhatsApp Business integration · Instagram DM integration · real-time menu availability · online table booking · customer segmentation · personalised offers · sentiment analysis · multilingual chatbot (Hindi/Marathi) · voice chatbot · CRM integration · real-time marketing analytics.

## 16. Project structure
```
brew-delice/
├── app.py  config.py  requirements.txt  seed_demo.py  README.md
├── chatbot/ (nlp_engine, intent_classifier, response_engine, context_manager, analytics)
├── data/ (menu.json, business.json, platforms.json, intents.json)
├── database/chatbot.db   templates/ (index.html, dashboard.html)
├── static/ (css/style.css, js/main.js, js/chatbot.js, js/dashboard.js, images/)
├── tests/ (test_chatbot.py, take_screenshots.py)
└── documentation/ (report PDF, diagrams, screenshots, test_results)
```
