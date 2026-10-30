"""Arma una página por marca (proyectos/<marca>/index.html), la grilla de portfolio.html,
sitemap.xml y _redirects, a partir de assets/portfolio/detalle.js.

Correrlo cada vez que se suma o cambia un proyecto:
    python3 scripts/generar_paginas.py
"""
import html, json, re, unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import unquote, quote

RAIZ = Path(__file__).resolve().parent.parent
SITIO = 'https://bulletcreativeagency.com'

# servicios que se mencionan en la descripción (chips del proyecto)
SERV = [(r'redes|social', 'Social media'), (r'dise[ñn]o', 'Diseño gráfico'), (r'branding|identidad|logo|naming', 'Branding'),
        (r'audiovisual|contenido|fotogr|video|producci', 'Contenido'), (r'pauta|campa[ñn]|ads|meta|google', 'Pauta'),
        (r'web|p[áa]gina|sitio|tienda online|e-?commerce', 'Web'), (r'influencer', 'Influencers')]


def slug(nombre):
    s = nombre.replace('´', '').replace("'", '')
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]+', '-', s).strip('-')


def corto(texto, n=155):
    t = ' '.join(texto.split())
    return t if len(t) <= n else t[:n].rsplit(' ', 1)[0].rstrip(',.;:') + '…'


def esc(t):
    return html.escape(t, quote=True)


def contenido(i, p, total, sig, ant):
    chips = ''.join(f'<span>{n}</span>' for r, n in SERV if re.search(r, p['desc'], re.I))
    fotos = [m for m in p['media'] if m['t'] == 'i']
    gal = []
    for m in p['media']:
        full = ' full' if m['w'] > m['h'] * 1.15 else ''
        if m['t'] == 'v':
            gal.append(f'<div class="m vid rv{full}" style="aspect-ratio:{m["w"]}/{m["h"]}"><video data-src="/{m["src"]}" poster="/{m["poster"]}" muted loop playsinline preload="none"></video></div>')
        else:
            gal.append(f'<div class="m rv{full}" style="aspect-ratio:{m["w"]}/{m["h"]}" data-k="{fotos.index(m)}"><img src="/{m["src"]}" alt="{esc(p["name"])}: trabajo de BULLET" loading="lazy" width="{m["w"]}" height="{m["h"]}"></div>')
    desc = '<br>'.join(esc(l) for l in p['desc'].split('\n') if l.strip())
    return f'''  <header class="pj-head wrap">
    <div class="crumbs rv"><a href="/portfolio.html">← Portafolio</a><span>Proyecto {i + 1:02d} / {total}</span></div>
    <h1 class="rv">{esc(p["name"])}<b>.</b></h1>
    <div class="pj-row">
      <p class="rv">{desc}</p>
      <div class="chips rv">{chips}</div>
    </div>
  </header>
  <div class="wrap">
    <div class="pj-cover" id="cover"><img src="/{p["cover_src"]}" alt="{esc(p["name"])}"></div>
    <div class="gal">
      {(chr(10) + '      ').join(gal)}
    </div>
    <a class="next rv" href="/proyectos/{sig["s"]}/">
      <div class="lbl"><div><small>Siguiente proyecto</small><strong>{esc(sig["name"])}</strong></div><span class="go"><i>→</i>Ver proyecto</span></div>
      <div class="pic"><img src="/{sig["cover_src"]}" alt="{esc(sig["name"])}" loading="lazy"></div>
    </a>
    <div class="others"><a href="/proyectos/{ant["s"]}/">← {esc(ant["name"])}</a><span></span><a href="/portfolio.html">Ver todos los proyectos</a></div>
  </div>'''


def main():
    D = json.loads((RAIZ / 'assets/portfolio/detalle.js').read_text().split('=', 1)[1].strip().rstrip(';'))
    for p in D:
        p['s'] = slug(p['name'])
    assert len({p['s'] for p in D}) == len(D), 'hay dos marcas con el mismo nombre'

    plantilla = (RAIZ / 'scripts/plantilla-proyecto.html').read_text()
    salida = RAIZ / 'proyectos'
    for viejo in salida.glob('*/index.html'):
        viejo.unlink()
    for i, p in enumerate(D):
        url = f'{SITIO}/proyectos/{p["s"]}/'
        nombre = p['name']
        jsonld = {'@context': 'https://schema.org', '@graph': [
            {'@type': 'CreativeWork', 'name': f'{nombre} — BULLET', 'description': corto(p['desc'], 300), 'url': url,
             'image': f'{SITIO}/{p["cover_src"]}', 'creator': {'@id': f'{SITIO}/#bullet'}},
            {'@type': 'BreadcrumbList', 'itemListElement': [
                {'@type': 'ListItem', 'position': 1, 'name': 'Inicio', 'item': f'{SITIO}/'},
                {'@type': 'ListItem', 'position': 2, 'name': 'Portafolio', 'item': f'{SITIO}/portfolio.html'},
                {'@type': 'ListItem', 'position': 3, 'name': nombre, 'item': url}]}]}
        pag = (plantilla
               .replace('{{TITULO}}', esc(f'{nombre} — Portafolio BULLET, agencia creativa en Mar del Plata'))
               .replace('{{NOMBRE}}', esc(nombre))
               .replace('{{DESC}}', esc(corto(p['desc'])))
               .replace('{{URL}}', url)
               .replace('{{OG_IMG}}', f'{SITIO}/{p["cover_src"]}')
               .replace('{{JSONLD}}', json.dumps(jsonld, ensure_ascii=False).replace('</', '<\\/'))
               .replace('{{CONTENIDO}}', contenido(i, p, len(D), D[(i + 1) % len(D)], D[i - 1])))
        (salida / p['s']).mkdir(parents=True, exist_ok=True)
        (salida / p['s'] / 'index.html').write_text(pag)
    for vacia in salida.iterdir():
        if vacia.is_dir() and not any(vacia.iterdir()):
            vacia.rmdir()

    # grilla del portafolio, escrita en el HTML para que Google la lea sin JS
    grilla = '\n'.join(
        f'    <a class="work rv" href="/proyectos/{p["s"]}/"><div class="pic"><img src="{p["img"]}" alt="{esc(p["name"])}" loading="{"eager" if i < 6 else "lazy"}"><span class="tag">Ver proyecto</span></div></a>'
        for i, p in enumerate(D))
    pf = RAIZ / 'portfolio.html'
    pf.write_text(re.sub(r'(<!-- grilla -->).*?(\n\s*<!-- /grilla -->)', lambda m: m[1] + '\n' + grilla + m[2], pf.read_text(), flags=re.S))

    # mapa del sitio
    hoy = date.today().isoformat()
    urls = [f'{SITIO}/', f'{SITIO}/portfolio.html', f'{SITIO}/nosotros.html'] + [f'{SITIO}/proyectos/{p["s"]}/' for p in D]
    (RAIZ / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                      + ''.join(f'  <url><loc>{u}</loc><lastmod>{hoy}</lastmod></url>\n' for u in urls) + '</urlset>\n')

    # redirecciones permanentes (301) desde las direcciones viejas de Wix y de proyecto.html?p=
    reglas = ['# Generado por scripts/generar_paginas.py — no editar a mano',
              '/acerca-de          /nosotros.html   301', '/acerca-de/         /nosotros.html   301',
              '/servicios          /#servicios      301', '/servicios/         /#servicios      301',
              '/contacto           /#contacto       301', '/contacto/          /#contacto       301',
              '/portfolio          /portfolio.html  301', '/portfolio/         /portfolio.html  301']
    for p in D:
        viejos = {p['slug'], unquote(p['slug']), unicodedata.normalize('NFC', unquote(p['slug'])),
                  quote(unicodedata.normalize('NFC', unquote(p['slug'])))}
        for v in sorted(viejos):
            reglas.append(f'/portfolio-collections/my-portfolio/{v}  /proyectos/{p["s"]}/  301!')
        for v in sorted({p['slug'], unquote(p['slug'])}):
            reglas.append(f'/proyecto.html  p={v}  /proyectos/{p["s"]}/  301!')
    reglas += ['/portfolio-collections/*  /portfolio.html  301!', '/proyecto.html  /portfolio.html  301!']
    (RAIZ / '_redirects').write_text('\n'.join(reglas) + '\n')
    print(f'{len(D)} proyectos, {len(urls)} URLs en el sitemap, {len(reglas) - 1} redirecciones')


if __name__ == '__main__':
    main()
