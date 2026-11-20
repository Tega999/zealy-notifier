import os, re, json, requests
from playwright.sync_api import sync_playwright

urls = [u for u in re.split(r"[\s,]+", os.environ["ZEALY_URL"]) if u.startswith("http")]
f = "seen.txt"
try:
    data = json.load(open(f))
except Exception:
    data = {}

def send(text):
    requests.post(
        f"https://api.telegram.org/bot{os.environ['BOT_TOKEN']}/sendMessage",
        data={"chat_id": os.environ["CHAT_ID"], "text": text[:4000]})

with sync_playwright() as p:
    b = p.chromium.launch()
    for url in urls:
        try:
            pg = b.new_page()
            pg.goto(url, timeout=60000)
            pg.wait_for_timeout(10000)
            lines = {l.strip() for l in pg.inner_text("body").splitlines() if len(l.strip()) > 3}
            pg.close()
        except Exception as e:
            print("Failed:", url, e)
            continue
        if not lines:
            print("Empty page:", url)
            continue
        old = set(data.get(url, []))
        new = lines - old
        if old and new:
            parts = url.split("/")
            name = parts[4] if len(parts) > 4 else url
            send(f"New on Zealy ({name}):\n" + "\n".join(sorted(new)[:15]) + f"\n\n{url}")
        data[url] = sorted(old | lines)
    b.close()

json.dump(data, open(f, "w"))
