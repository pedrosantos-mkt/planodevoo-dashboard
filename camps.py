import requests,os,json
G='https://graph.facebook.com/v21.0/'
T=open(os.path.expanduser('~/.config/meta/token')).read().strip()
camps={}
for acc in ['act_171474008015977','act_696363384474339']:
  for v in ['PLANODEVOO','PLANO DE VOO','PLANO_DE_VOO']:
    url=G+acc+'/campaigns'; p={'access_token':T,'fields':'id,name,effective_status,objective,created_time,daily_budget,lifetime_budget','limit':500,'filtering':json.dumps([{'field':'name','operator':'CONTAIN','value':v}])}
    while url:
        r=requests.get(url,params=p,timeout=60).json()
        if 'error' in r: print(acc,r); break
        for c in r['data']: c['acc']=acc; camps[c['id']]=c
        url=r.get('paging',{}).get('next'); p=None
for c in sorted(camps.values(),key=lambda c:c['created_time']): print(c['acc'][-4:],c['id'],c['effective_status'],c['created_time'][:10],c['objective'],c.get('daily_budget'),c['name'])
json.dump(list(camps.values()),open('raw/camps.json','w'))
