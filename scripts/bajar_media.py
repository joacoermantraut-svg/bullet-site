"""Baja a assets/proyectos/ las fotos y videos de cada proyecto (desde Wix) y
reescribe assets/portfolio/detalle.js con las rutas locales.
Uso: python3 scripts/bajar_media.py  (desde ~/bullet-site)"""
import json, os, subprocess, concurrent.futures as cf

DATA = 'assets/portfolio/detalle.js'
W = 'https://static.wixstatic.com/media/'

def curl(url, out):
    if os.path.exists(out) and os.path.getsize(out) > 0:
        return True
    r = subprocess.run(['curl', '-sf', '--retry', '3', '-o', out, url])
    return r.returncode == 0

def jobs_for(n, p):
    d = f'assets/proyectos/{n:02d}'
    os.makedirs(d, exist_ok=True)
    jobs = [(f"{W}{p['cover']}/v1/fit/w_1800,h_1800,q_82,enc_jpg/c.jpg", f'{d}/portada.jpg')]
    p['cover_src'] = f'{d}/portada.jpg'
    for k, m in enumerate(p['media'], 1):
        if m['t'] == 'i':
            m['src'] = f'{d}/{k:02d}.jpg'
            jobs.append((f"{W}{m['id']}/v1/fit/w_1600,h_2400,q_82,enc_jpg/f.jpg", m['src']))
        else:
            m['src'] = f'{d}/{k:02d}.mp4'
            m['poster'] = f'{d}/{k:02d}-poster.jpg'
            jobs.append((f"https://video.wixstatic.com/video/{m['id']}/720p/mp4/file.mp4", m['src']))
            jobs.append((f"{W}{m['id']}f000.jpg/v1/fit/w_1000,h_1800,q_80,enc_jpg/p.jpg", m['poster']))
    return jobs

def main():
    raw = open(DATA).read()
    d = json.loads(raw[raw.index('['):raw.rindex(']') + 1])
    jobs = [j for n, p in enumerate(d, 1) for j in jobs_for(n, p)]
    with cf.ThreadPoolExecutor(12) as ex:
        ok = list(ex.map(lambda j: curl(*j), jobs))
    fallidos = [j[1] for j, o in zip(jobs, ok) if not o]
    print(f'{sum(ok)}/{len(jobs)} archivos', 'fallidos:', fallidos[:10])
    open(DATA, 'w').write('window.DETALLE=' + json.dumps(d, ensure_ascii=False) + ';\n')

if __name__ == '__main__':
    main()
