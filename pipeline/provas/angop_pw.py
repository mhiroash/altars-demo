from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(user_agent="AltarsDemoPipeline/0.1 (contacto: ellocene-lda; uso editorial demo)")
    try:
        r = pg.goto("https://www.angop.ao/", timeout=45000, wait_until="domcontentloaded")
        pg.wait_for_timeout(6000)
        print("status:", r.status if r else None)
        print("url:", pg.url)
        print("title:", pg.title())
        links = pg.eval_on_selector_all("a", "els => els.map(e => e.getAttribute('href')).filter(h => h && h.includes('.aspx') || h && h.includes('/angop/')).slice(0,10)")
        print("sample links:", links)
        body_len = pg.eval_on_selector("body", "e => e.innerText.length")
        print("body text length:", body_len)
    except Exception as e:
        print("ERRO:", type(e).__name__, str(e)[:300])
    b.close()
