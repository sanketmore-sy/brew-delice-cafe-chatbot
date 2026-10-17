"""Set a VERIFIED ordering link in one command (after you have opened the listing and confirmed it is Brew Delice Café, Nigdi).
Usage:  python set_platform.py zomato "https://www.zomato.com/pune/....."
        python set_platform.py swiggy "https://www.swiggy.com/restaurants/....."
        python set_platform.py swiggy --off        (disable again)"""
import json, os, sys
from datetime import date
F = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "platforms.json")
DOM = {"zomato": "zomato.com", "swiggy": "swiggy.com", "toing": "toing"}
if len(sys.argv) < 3 or sys.argv[1] not in DOM:
    sys.exit(__doc__)
d = json.load(open(F, encoding="utf-8")); p = d["platforms"][sys.argv[1]]
if sys.argv[2] == "--off":
    p.update(available=False, url="", verified_on=None)
else:
    url = sys.argv[2].strip()
    if not url.startswith("https://") or DOM[sys.argv[1]] not in url or "google." in url:
        sys.exit("URL must be an https link on " + DOM[sys.argv[1]])
    p.update(available=True, url=url, verified_on=str(date.today()))
json.dump(d, open(F, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(sys.argv[1], "->", "ENABLED" if p["available"] else "disabled", "(restart not needed)")
