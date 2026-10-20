#!/usr/bin/env python3
"""Run a saved, bounded query plan; one request/job, preserve raw responses and errors."""
import argparse,datetime,getpass,json,os,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'xhs-follower-growth-chart/scripts'))
from redfox_transport import post_json
p=argparse.ArgumentParser();p.add_argument('--plan',required=True);p.add_argument('--out',required=True);a=p.parse_args()
plan=json.loads(pathlib.Path(a.plan).read_text());out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
key=os.environ.get('REDFOX_API_KEY') or getpass.getpass('Redfox key (hidden): ')
for job in plan:
 target=out/(job['query_id']+'.json')
 if target.exists(): print(job['query_id'],'already saved; skipped',flush=True);continue
 entry={**job,'collected_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()}
 try:
  r=post_json(job['url'],job['payload'],{'X-API-KEY':key,'REDFOX_API_KEY':key},timeout=35)
  entry.update(status='response',response=r);d=r.get('data')
  print(job['query_id'],'code',r.get('code'),'fields',list(d) if isinstance(d,dict) else len(d) if isinstance(d,list) else None,flush=True)
 except Exception as e:
  entry.update(status='error',error=str(e).replace(key,'[REDACTED]'));print(job['query_id'],entry['error'],flush=True)
 target.write_text(json.dumps(entry,ensure_ascii=False,indent=2))
