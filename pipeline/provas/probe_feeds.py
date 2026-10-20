import urllib.request, xml.etree.ElementTree as ET, re
UA = "AltarsDemoPipeline/0.1 (contacto: ellocene-lda; uso editorial demo)"
SAFE = {"amp","lt","gt","quot","apos"}
def clean(data: bytes) -> bytes:
    txt = data.decode("utf-8", errors="replace")
    def repl(m):
        e = m.group(1)
        if e in SAFE or re.fullmatch(r"#\d+", e) or re.fullmatch(r"#x[0-9a-fA-F]+", e):
            return m.group(0)
        return " "
    return re.sub(r"&(\w+);", repl, txt).encode("utf-8")
feeds = {
    "correiokianda": "https://www.correiokianda.info/feed/",
    "makaangola": "https://www.makaangola.org/feed/",
    "redeangola": "https://redeangola.info/feed",
    "eco": "https://eco.sapo.pt/rss/",
    "rtp": "https://www.rtp.pt/noticias/rss",
}
for name, url in feeds.items():
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    data = urllib.request.urlopen(req, timeout=25).read()
    root = ET.fromstring(clean(data))
    items = root.findall(".//item")
    print(f"=== {name}: {len(items)} items ===")
    it = items[0]
    for child in list(it)[:14]:
        tag = child.tag.split('}')[-1]
        txt = (child.text or "").strip().replace("\n"," ")[:90]
        print(f"  {tag}: {txt}")
