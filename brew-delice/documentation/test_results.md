# Test results

| Test ID | Input | Expected Result | Actual Result | Status |
|---|---|---|---|---|
| T01 | Hi | Greeting 'Welcome to Brew Delice Café' + View Menu button | intent=greeting; buttons=['🍽 View Menu', '⭐ Main Attractions', '🛵 Order Online', '📍 Find Us', '❓ Ask a Question'] | PASS |
| T02 | Hello | Greeting intent | intent=greeting | PASS |
| T03 | hii (typo/variation) | Greeting intent | intent=greeting | PASS |
| T04 | Show menu | Menu with Coffee 40, Burger 59, French Fries 59, Pizza 99 | intent=menu; items={'coffee': 40, 'burger': 59, 'fries': 59, 'pizza': 99} | PASS |
| T05 | what do you have? | Menu intent (natural language) | intent=menu | PASS |
| T06 | Main attractions | Main Attractions list with 4 items | intent=main_attractions; n=4 | PASS |
| T07 | [View Menu button] | Menu displayed via button action | intent=menu | PASS |
| T08 | Coffee | Coffee card ₹40 with View Details and Order Now buttons | price=40; buttons=['👁 View Details', '🛒 Order Now', '🍽 View Menu'] | PASS |
| T09 | coffee price? | Coffee is ₹40 | Coffee is ₹40. | PASS |
| T10 | how much is burger? | Burger is ₹59 | Burger is ₹59. | PASS |
| T11 | french fries price | French Fries ₹59 | French Fries is ₹59. | PASS |
| T12 | how much is pizza | Pizza is ₹99 | Pizza is ₹99. | PASS |
| T13 | Where are you located? | Address Pradhikaran, Nigdi, 411044 + Get Directions | 📍 Brew Delice Café is at Pradhikaran, Nigdi, Pimpri-Chinchwad, Maharashtra – 411044. / Note: the map button opens a Goog | PASS |
| T14 | open google maps | Location intent; button URL points to google.com/maps | urls=['https://www.google.com/maps/search/?api=1&query=Brew+Delice+', 'https://www.google.com/search?q=Brew+Delice+Caf%C3%A9+Pradhi'] | PASS |
| T15 | how can I order? | 'Order on Swiggy' button linking to the café's real Swiggy page; no Zomato/Toing link | links=['https://www.swiggy.com/menu/1376195?source=sharing'] | PASS |
| T16 | are you on zomato? | Honest 'could not verify' answer, no Zomato link | I couldn't verify a Brew Delice Café listing on Zomato yet, so I won't share a l | PASS |
| T17 | are you on swiggy? | Swiggy intent; confirms availability + real Swiggy link | intent=swiggy | PASS |
| T36 | full menu | One menu list per category; all 30 items shown | intent=fullmenu; items=30 | PASS |
| T37 | mojito | Category intent listing the 4 mojitos | intent=category; ['Mint Mojito', 'Blue Currant Mojito', 'Green Apple Mojito', 'Mango Mojito'] | PASS |
| T38 | double tikki burger price | Item from menu card: ₹70 | Double Tikki Burger is ₹70. | PASS |
| T39 | veg cheese burger | Longest match: Veg Cheese Burger (₹50), not plain Burger | item | PASS |
| T40 | I want to order oreo shake | Swiggy link shown for a card item | intent=order | PASS |
| T41 | extra cheese | Add-on ₹10 shown, no Order button | ['👁 View Details', '🍽 View Menu'] | PASS |
| T42 | mojto (typo) | Fuzzy-matched to the Mojito category | intent=category | PASS |
| T18 | toing | Toing intent, no fake link | intent=toing | PASS |
| T19 | what do you recommend? | Recommendation without invented 'bestseller' claims | I can't claim a "bestseller" without real sales data, but here are good starting points: ☕ | PASS |
| T20 | I want to enquire → name → contact → message | Enquiry stored in SQLite; 'Your enquiry has been recorded' | rows_in_db=1 | PASS |
| T21 | Enquiry with invalid contact '12' | Validation error, not stored | Please enter a valid phone number (7-15 digits) or email address. | PASS |
| T22 | what is the capital of india | Fallback reply with help options | intent=fallback | PASS |
| T23 | (empty message) | Friendly prompt; nothing stored | Please type a message — for example “show menu” or “coffee price”. 😊 | PASS |
| T24 | Coffee → How do I order it? | Context: answer is about Coffee | item=coffee; Coffee (₹40) is available for online ordering through the ve | PASS |
| T25 | Burger → How much? | Context: 'Burger is ₹59.' | Burger is ₹59. | PASS |
| T26 | burgur price (typo) | Typo tolerated → Burger ₹59 | Burger is ₹59. | PASS |
| T27 | what are your timings? | Does NOT invent opening hours | 🕐 Opening hours haven't been verified yet, so I won't guess. / Please check the  | PASS |
| T28 | thanks / bye | Thanks and goodbye intents | thanks, goodbye | PASS |
| T29 | Feedback 👎 → 'What information were you looking for?' | Stored in feedback table | row=(0, 'Opening hours') | PASS |
| T30 | Order Now when a platform IS verified (simulated) | Only verified platform shown, new-tab link | platforms=['zomato'] | PASS |
| T31 | Name '<b>x</b>' on enquiry form | Rejected by validation (HTML not allowed) | status=400 | PASS |
| T32 | SQL injection text in message | Stored literally; tables intact | status=200; enquiries_table_rows=2 | PASS |
| T33 | menu.json prices | Main Attractions unchanged: Coffee 40, Burger 59, French Fries 59, Pizza 99 | {'coffee': 40, 'burger': 59, 'fries': 59, 'pizza': 99} | PASS |
| T34 | Dashboard + analytics API | /dashboard 200; KPIs and both rates present | conversations=37; enq_rate=2.7%; ctr=21.4% | PASS |
| T35 | platforms.json / business.json audit | Only Swiggy available (real URL); Zomato/Toing off; no invented phone/hours | available=['swiggy']; hours=None; phone=None | PASS |
