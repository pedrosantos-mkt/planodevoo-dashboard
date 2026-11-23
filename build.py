# raw/raw.json -> site/data.json (linhas granulares; a página recorta por período e calcula tudo)
import json, os, re, datetime as dt
AQUI = os.path.dirname(os.path.abspath(__file__))
CFG = json.load(open(os.path.join(AQUI, 'metas.json')))
R = json.load(open(os.path.join(AQUI, 'raw', 'raw.json')))
TZ = dt.timezone(dt.timedelta(hours=-3))
act = lambda r, t: sum(float(a['value']) for a in r.get('actions', []) if a['action_type'] == t)

def pagina(url):
    slug = re.sub(r'[?#].*', '', url or '').rstrip('/').split('/')[-1]
    return CFG['paginas'].get(slug, slug or '—')

# anúncios: página de destino e miniatura
ad_pag, cre = {}, {}
for a in R['ads']:
    c = a.get('creative') or {}
    links = [u.get('website_url') for u in (c.get('asset_feed_spec') or {}).get('link_urls', [])]
    links += [((c.get('object_story_spec') or {}).get('link_data') or {}).get('link')]
    links = [l for l in links if l]
    ad_pag[a['id']] = pagina(links[0]) if links else '—'
    n = a['name']
    d = cre.setdefault(n, {'thumb': '', 'ativos': 0, 'anuncios': 0})
    d['thumb'] = d['thumb'] or c.get('thumb400') or c.get('thumbnail_url') or ''
    d['anuncios'] += 1; d['ativos'] += a.get('effective_status') == 'ACTIVE'

camps, cidx = [], {}
def ci(id_, nome):
    if id_ not in cidx:
        cidx[id_] = len(camps)
        lp = re.search(r'LP (V\d+)', nome)
        camps.append({'id': id_, 'nome': nome, 'temp': 'Quente' if 'QUENTE' in nome else ('Frio' if 'FRIO' in nome else 'Sem tag'),
                      'lp': 'LP ' + lp.group(1) if lp else '—', 'teste': 'Página' if 'TESTE_PAGINA' in nome else ('Criativo' if 'TESTE_CRIATIVO' in nome else '')})
    return cidx[id_]
nomes = []; nidx = {}
def ni(n):
    if n not in nidx: nidx[n] = len(nomes); nomes.append(n)
    return nidx[n]
paginas = []; pidx = {}
def pi(p):
    if p not in pidx: pidx[p] = len(paginas); paginas.append(p)
    return pidx[p]
conj = []; jidx = {}
def ji(n):
    if n not in jidx: jidx[n] = len(conj); conj.append(n)
    return jidx[n]

md = []
for r in R['ins']:
    md.append([r['date_start'], ci(r['campaign_id'], r['campaign_name']), ni(r['ad_name']), pi(ad_pag.get(r['ad_id'], '—')), ji(r['adset_name']),
               round(float(r['spend']), 2), int(r['impressions']), int(r.get('inline_link_clicks', 0)), int(act(r, 'landing_page_view')), int(act(r, 'lead') + act(r, 'offsite_conversion.fb_pixel_lead'))])

FAIXAS = ['Menor que 100 mil por mês', '100 mil a 200 mil por mês', '200 mil a 499 mil por mês', '500 mil a 999 mil por mês',
          '1 milhão a 3 milhões por mês', '3 milhões a 6 milhões por mês', 'Maior que 6 milhões por mês']
v = lambda s, k: next((x['value'] for x in s['values'] if x['name'] == k), '')
nome_c = {c['nome']: i for i, c in enumerate(camps)}
seen = set(); leads = []; envios = 0
for s in sorted(R['subs'], key=lambda s: s['submittedAt']):
    t = dt.datetime.fromtimestamp(s['submittedAt'] / 1000, TZ)
    if t.date().isoformat() < CFG['inicio']: continue
    e = v(s, 'email').strip().lower(); src = v(s, 'utm_source').lower()
    if not e or 'grupor1' in e or 'teste' in e or 'teste' in src: continue
    envios += 1
    if e in seen: continue
    seen.add(e)
    camp = v(s, 'utm_campaign')
    c = nome_c.get(camp, -1)
    term = v(s, 'utm_term').strip()
    fx = v(s, 'annualrevenue')
    leads.append([t.date().isoformat(), c, ni(term) if term else -1, pi(pagina(s.get('pageUrl'))), FAIXAS.index(fx) if fx in FAIXAS else -1,
                  0 if fx == FAIXAS[0] or fx not in FAIXAS else 1, 1 if src.startswith(('facebook', 'meta', 'fb', 'ig', 'instagram')) else 0])

agora = dt.datetime.fromisoformat(R['coleta'])
out = {'cfg': CFG, 'coleta': R['coleta'], 'hora': agora.strftime('%Hh%M'),
       'frac': round((agora.hour * 60 + agora.minute) / 1440, 3),
       'camps': camps, 'nomes': nomes, 'paginas': paginas, 'conj': conj, 'faixas': FAIXAS, 'cre': cre, 'md': md, 'leads': leads, 'envios': envios}
os.makedirs(os.path.join(AQUI, 'site'), exist_ok=True)
json.dump(out, open(os.path.join(AQUI, 'site', 'data.json'), 'w'), ensure_ascii=False, separators=(',', ':'))
sp = sum(r[5] for r in md); print('gasto', round(sp), 'leads', len(leads), 'qualif', sum(l[5] for l in leads), 'sem camp', sum(l[1] < 0 for l in leads), 'lpv', sum(r[8] for r in md))
import collections
print(collections.Counter((camps[r[1]]['lp'], paginas[r[3]]) for r in md))
print(collections.Counter((camps[l[1]]['lp'] if l[1] >= 0 else '-', paginas[l[3]]) for l in leads))
print(sorted({r[0] for r in md}))
