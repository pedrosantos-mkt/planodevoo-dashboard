# Coleta Meta (anúncio × dia) + HubSpot (form LIVE - Plano de Voo 2027) das campanhas [PLANODEVOO]
import requests, os, json, time, datetime as dt
AQUI = os.path.dirname(os.path.abspath(__file__)); RAW = os.path.join(AQUI, 'raw'); os.makedirs(RAW, exist_ok=True)
CFG = json.load(open(os.path.join(AQUI, 'metas.json')))
TZ = dt.timezone(dt.timedelta(hours=-3))
G = 'https://graph.facebook.com/v21.0/'
def tok(env, arq):
    return os.environ.get(env) or open(os.path.expanduser(arq)).read().strip()
T = tok('META_TOKEN', '~/.config/meta/token')
H = {'Authorization': 'Bearer ' + tok('HUBSPOT_TOKEN', '~/.config/hubspot/token')}
ACC = CFG['conta']; FILTRO = CFG['filtro_campanha']

def meta(url, p):
    out = []
    while url:
        for tent in range(8):
            try:
                r = requests.get(url, params=p, timeout=180).json()
            except Exception as e:
                print('rede', e); time.sleep(15); continue
            if 'error' in r:
                e = r['error']; print('meta erro', e.get('code'), e.get('message'))
                if e.get('code') in (1, 2, 4, 17, 80004, 613) or e.get('is_transient'):
                    time.sleep(min(300, 30 * (tent + 1))); continue
                raise SystemExit(1)
            break
        else:
            raise SystemExit('Meta não respondeu')
        out += r['data']; url = r.get('paging', {}).get('next'); p = None
    return out

hoje = dt.datetime.now(TZ).date()
ini = CFG['inicio']; fim = min(hoje.isoformat(), CFG['fim'])
filt = json.dumps([{'field': 'campaign.name', 'operator': 'CONTAIN', 'value': FILTRO}])
ins = meta(G + ACC + '/insights', {'access_token': T, 'level': 'ad', 'time_increment': 1, 'limit': 500,
      'fields': 'campaign_id,campaign_name,adset_name,ad_id,ad_name,spend,impressions,inline_link_clicks,actions',
      'time_range': json.dumps({'since': ini, 'until': fim}), 'filtering': filt})
print('insights', len(ins))
ads = meta(G + ACC + '/ads', {'access_token': T, 'limit': 200, 'filtering': filt,
      'fields': 'name,effective_status,campaign_id,creative{thumbnail_url,image_url,object_story_spec{link_data{link,picture},video_data{image_url}},asset_feed_spec{link_urls,images}}'})
print('anúncios', len(ads))
# Miniatura maior que a de 64px: pede thumbnail 400px pelos ids dos creatives
cids = list({a['creative']['id'] for a in ads if a.get('creative')})
thumbs = {}
for i in range(0, len(cids), 25):
    try:
        j = requests.get(G, params={'access_token': T, 'ids': ','.join(cids[i:i+25]), 'fields': 'thumbnail_url', 'thumbnail_width': 400, 'thumbnail_height': 400}, timeout=60).json()
        for k, v in j.items():
            if isinstance(v, dict) and v.get('thumbnail_url'): thumbs[k] = v['thumbnail_url']
    except Exception as e:
        print('thumbs', e)
for a in ads:
    c = a.get('creative') or {}
    if c.get('id') in thumbs: c['thumb400'] = thumbs[c['id']]

subs = []; after = None
while True:
    p = {'limit': 50}
    if after: p['after'] = after
    r = requests.get('https://api.hubapi.com/form-integrations/v1/submissions/forms/' + CFG['form_hubspot'], headers=H, params=p, timeout=60)
    if r.status_code == 429: time.sleep(10); continue
    r.raise_for_status(); j = r.json()
    subs += j.get('results', []); after = j.get('paging', {}).get('next', {}).get('after')
    if not after: break
print('envios', len(subs))
json.dump({'ins': ins, 'ads': ads, 'subs': subs, 'coleta': dt.datetime.now(TZ).isoformat(timespec='minutes')}, open(os.path.join(RAW, 'raw.json'), 'w'))
