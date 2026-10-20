from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36")
    try:
        r = pg.goto("https://www.angop.ao/", timeout=60000, wait_until="load")
        pg.wait_for_timeout(15000)
        print("status:", r.status if r else None, "| url:", pg.url)
        body_len = pg.eval_on_selector("body", "e => e.innerText.length")
        links = pg.eval_on_selector_all("a", "els => els.map(e => e.getAttribute('href')).filter(Boolean).slice(0,15)")
        print("body_len:", body_len)
        print("links:", links[:15])
    except Exception as e:
        print("ERRO:", type(e).__name__, str(e)[:200])
    b.close()
