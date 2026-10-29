"""Baja nombre, descripción y galería (en orden) de cada proyecto del portfolio de Wix.
Uso: python3 scripts/scrape_proyectos.py  (desde ~/bullet-site)"""
import re, json, html, urllib.request, concurrent.futures as cf

SRC = 'assets/portfolio/proyectos.js'
OUT = 'assets/portfolio/detalle.js'
ID = re.compile(r'd2f004_([0-9a-f]{32})(f000\.jpg|~mv2\.(?:jpe?g|png|webp|gif))')

def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    return urllib.request.urlopen(req, timeout=40).read().decode('utf-8', 'replace')

def meta(h, prop):
    m = re.search(r'property="og:%s" content="([^"]*)"' % prop, h)
    return html.unescape(m.group(1)).strip() if m else ''

def parse(p):
    h = fetch(p['url'])
    items, seen = [], set()
    for m in re.finditer(r'data-hook="image-item"[^>]*style="width:(\d+)px;height:(\d+)px', h):
        idm = ID.search(h, m.end(), m.end() + 1500)
        if not idm: continue
        key, ext = idm.groups()
        if key in seen: continue
        seen.add(key)
        w, hh = int(m.group(1)), int(m.group(2))
        if ext == 'f000.jpg':
            items.append({'t': 'v', 'id': 'd2f004_' + key, 'w': w, 'h': hh})
        else:
            items.append({'t': 'i', 'id': 'd2f004_' + key + ext, 'w': w, 'h': hh})
    desc = meta(h, 'description')
    return {**p, 'desc': desc, 'media': items}

def main():
    raw = open(SRC).read()
    proyectos = json.loads(raw[raw.index('['):raw.rindex(']') + 1])
    with cf.ThreadPoolExecutor(6) as ex:
        res = list(ex.map(parse, proyectos))
    for r in res:
        print(f"{r['name'][:28]:28} {len(r['media']):3} items  desc:{len(r['desc'])}")
    open(OUT, 'w').write('window.DETALLE=' + json.dumps(res, ensure_ascii=False) + ';\n')

if __name__ == '__main__':
    main()
