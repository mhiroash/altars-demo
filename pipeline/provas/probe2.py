import urllib.request, xml.etree.ElementTree as ET, re
UA = "AltarsDemoPipeline/0.1 (contacto: ellocene-lda; uso editorial demo)"
SAFE = {"amp","lt","gt","quot","apos"}
def clean(data):
    txt = data.decode("utf-8", errors="replace")
    return re.sub(r"&(\w+);", lambda m: m.group(0) if m.group(1) in SAFE or m.group(1).startswith("#") else " ", txt).encode()
for name, url in [("makaangola","https://www.makaangola.org/feed/"), ("correiokianda","https://www.correiokianda.info/feed/")]:
    data = urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=25).read()
    root = ET.fromstring(clean(data))
    items = root.findall(".//item")
    print(f"=== {name}: {len(items)} items ===")
    for i, it in enumerate(items[:3]):
        tags = [c.tag.split('}')[-1] for c in it]
        enc = it.find("{http://purl.org/rss/1.0/modules/content/}encoded")
        body_len = len(re.sub(r"<[^>]+>", " ", enc.text or "")) if enc is not None else 0
        print(f"  [{i}] {it.find('title').text[:60]} | tags={set(tags)} | corpo~{body_len} chars")
        pd = it.find("pubDate")
        print(f"      pubDate: {pd.text if pd is not None else None}")
