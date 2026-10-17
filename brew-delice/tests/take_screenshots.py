"""Runs the faculty demo flow in a real browser, checks console errors / broken assets and saves screenshots.
Usage:  (server running)  python tests/take_screenshots.py [base_url]"""
import os, sys, json
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5000"
OUT = os.path.join(os.path.dirname(__file__), "..", "documentation", "screenshots")
os.makedirs(OUT, exist_ok=True)
problems = []


def shot(page, name, **kw):
    page.screenshot(path=os.path.join(OUT, name), **kw)
    print("saved", name)


def chat_say(page, text):
    page.fill("#chatInput", text)
    page.press("#chatInput", "Enter")
    page.wait_for_timeout(1500)


with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
    page = ctx.new_page()
    page.on("console", lambda m: problems.append(("console", m.type, m.text)) if m.type == "error" else None)
    page.on("pageerror", lambda e: problems.append(("pageerror", str(e))))
    page.on("response", lambda r: problems.append(("http", r.status, r.url)) if r.status >= 400 else None)
    page.on("requestfailed", lambda r: problems.append(("reqfailed", r.url)) if "fonts.g" not in r.url and "maps.google" not in r.url and "cdnjs" not in r.url else None)

    page.goto(BASE); page.wait_for_timeout(1200)
    shot(page, "01_home.png")
    page.evaluate("document.getElementById('attractions').scrollIntoView()"); page.wait_for_timeout(1200)
    shot(page, "02_main_attractions.png")
    page.click("#attractions .card >> nth=3 >> text=View Details"); page.wait_for_timeout(900)
    shot(page, "02b_item_detail_modal.png"); page.keyboard.press("Escape")
    page.evaluate("document.getElementById('menu').scrollIntoView()"); page.wait_for_timeout(1200)
    shot(page, "03_full_menu.png")
    page.evaluate("document.getElementById('findus').scrollIntoView()"); page.wait_for_timeout(1500)
    shot(page, "08_find_us.png")
    # website enquiry form
    page.fill("#enqForm [name=name]", "Ananya Kulkarni"); page.fill("#enqForm [name=contact]", "9876543210")
    page.select_option("#enqForm [name=item]", "pizza"); page.fill("#enqForm [name=message]", "Do you take group orders for 8 people?")
    page.click("#enqForm button[type=submit]"); page.wait_for_timeout(900)
    shot(page, "09_enquiry_form.png")

    # --- chatbot demo sequence ---
    page.evaluate("window.scrollTo(0,0)"); page.click("#chatFab"); page.wait_for_timeout(900)
    shot(page, "04_chatbot_greeting.png")
    chat_say(page, "Hi")
    shot(page, "04b_chat_hi_response.png")
    page.click("#chatBody >> text=🍽 View Menu"); page.wait_for_timeout(1800)
    shot(page, "05_chatbot_menu.png")
    page.click(".mrow >> nth=0"); page.wait_for_timeout(1800)
    shot(page, "06_coffee_details.png")
    page.click("#chat >> text=👁 View Details"); page.wait_for_timeout(2200)
    shot(page, "06b_chat_item_details.png")
    page.click("#chat >> text=🛒 Order Now >> nth=-1"); page.wait_for_timeout(2200)
    shot(page, "07_order_platform_selection.png")
    chat_say(page, "Where are you located?")
    shot(page, "07b_chat_location.png")
    with ctx.expect_page() as pi:
        page.click("#chat >> text=🧭 Get Directions >> nth=-1")
    pi.value.close()
    chat_say(page, "show mojito")
    shot(page, "07d_chat_category.png")
    chat_say(page, "I want to order oreo shake")
    shot(page, "07e_chat_card_item_order.png")
    for q in ["burger price", "how much is pizza", "what do you recommend?", "are you on swiggy?", "thanks"]:
        chat_say(page, q)
    shot(page, "07c_chat_natural_language.png")
    page.click("#chat >> text=👎 No"); page.wait_for_timeout(1500); chat_say(page, "Wanted opening hours")
    chat_say(page, "I want to enquire"); chat_say(page, "Rohan Deshmukh"); chat_say(page, "rohan@example.com"); chat_say(page, "Is the cafe open on Sundays?")
    shot(page, "09b_chat_enquiry_done.png")

    page.goto(BASE + "/dashboard"); page.wait_for_timeout(2500)
    shot(page, "10_dashboard.png", full_page=True)

    # --- mobile ---
    m = b.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2, is_mobile=True, has_touch=True)
    mp = m.new_page()
    mp.on("pageerror", lambda e: problems.append(("pageerror-mobile", str(e))))
    mp.goto(BASE); mp.wait_for_timeout(1200)
    shot(mp, "11_mobile_home.png")
    overflow = mp.evaluate("document.documentElement.scrollWidth > window.innerWidth + 1")
    if overflow: problems.append(("mobile horizontal overflow",))
    mp.click("#chatFab"); mp.wait_for_timeout(800)
    mp.fill("#chatInput", "hi"); mp.press("#chatInput", "Enter"); mp.wait_for_timeout(1800)
    shot(mp, "12_mobile_chat.png")
    box = mp.evaluate("(()=>{const r=document.getElementById('chat').getBoundingClientRect();return [r.width,r.height,innerWidth,innerHeight]})()")
    print("mobile chat box", box)
    b.close()

print("PROBLEMS:", json.dumps(problems, indent=1) if problems else "none")
