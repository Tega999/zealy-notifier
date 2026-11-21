import os, re, json, time, requests
from playwright.sync_api import sync_playwright

urls = [u for u in re.split(r"[\s,]+", os.environ["ZEALY_URL"]) if u.startswith("http")]
f = "seen.txt"
try:
    data = {k: set(v) for k, v in json.load(open(f)).items()}
except Exception:
    data = {}

LOOP_SECONDS = 270   # how long each run keeps checking
EVERY = 20           # seconds between check cycles
start = time.time()

def send(text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{os.environ['BOT_TOKEN']}/sendMessage",
            data={"chat_id": os.environ["CHAT_ID"], "text": text[:4000]},
            timeout=20)
    except Exception as e:
        print("Telegram failed:", e)

def save():
    json.dump({k: sorted(v) for k, v in data.items()}, open(f, "w"))

def check(ctx, url):
    pg = ctx.new_page()
    try:
        pg.goto(url, timeout=60000)
        pg.wait_for_timeout(6000)
        lines = {l.strip() for l in pg.inner_text("body").splitlines() if len(l.strip()) > 3}
    except Exception as e:
        print("Failed:", url, e)
        return
    finally:
        pg.close()
    if not lines:
        print("Empty page:", url)
        return
    old = data.get(url, set())
    new = lines - old
    if old and new:
        parts = url.split("/")
        name = parts[4] if len(parts) > 4 else url
        send(f"New on Zealy ({name}):\n" + "\n".join(sorted(new)[:15]) + f"\n\n{url}")
    data[url] = old | lines

with sync_playwright() as p:
    b = p.chromium.launch()
    ctx = b.new_context()
    while True:
        t = time.time()
        for url in urls:
            check(ctx, url)
        save()
        if time.time() - start + EVERY > LOOP_SECONDS:
            break
        time.sleep(max(0, EVERY - (time.time() - t)))
    b.close()
save()
