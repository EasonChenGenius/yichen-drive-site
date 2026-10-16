"""Lighthouse cold profiles; use only the isolated QA service on port 8767."""
import os,json,subprocess,statistics
from pathlib import Path
root=Path(__file__).resolve().parents[1]
cli=os.environ['YICHEN_LIGHTHOUSE_CLI']
out=root/'output/playwright/perf-v56';out.mkdir(parents=True,exist_ok=True)
summary=[]
for name,url,preset,count in [('mobile-home','http://127.0.0.1:8767/','mobile',5),('mobile-enquiry','http://127.0.0.1:8767/#/enquiry?car=gl8','mobile',5),('desktop-home','http://127.0.0.1:8767/','desktop',1)]:
 runs=[]
 for n in range(count):
  target=out/f'{name}-{n+1}.json'
  cmd=['node',cli,url,'--output=json','--output-path='+str(target),'--chrome-flags=--headless=new --no-sandbox','--quiet','--only-categories=performance,accessibility,best-practices,seo']
  if preset=='desktop':cmd+=['--preset=desktop']
  subprocess.run(cmd,check=True)
  d=json.loads(target.read_text());result={'run':n+1,'lighthouseVersion':d['lighthouseVersion'],'fetchTime':d['fetchTime'],'scores':{k:round(v['score']*100) for k,v in d['categories'].items()},'metrics':{k:d['audits'][k].get('numericValue') for k in ['largest-contentful-paint','cumulative-layout-shift','total-blocking-time','total-byte-weight']}}
  runs.append(result);print(name,result,flush=True)
 metrics={k:{'median':statistics.median(r['metrics'][k] for r in runs),'worst':max(r['metrics'][k] for r in runs)} for k in runs[0]['metrics']}
 summary.append({'case':name,'url':url,'formFactor':preset,'throttlingMethod':'simulate','runs':runs,'aggregate':metrics,'passesTargets':metrics['largest-contentful-paint']['median']<=2500 and metrics['cumulative-layout-shift']['median']<=.1 and metrics['total-blocking-time']['median']<=200})
 (out/'summary.json').write_text(json.dumps(summary,indent=2))
