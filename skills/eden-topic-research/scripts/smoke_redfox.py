#!/usr/bin/env python3
"""Small, explicit Redfox acceptance batch; key stays in memory, raw evidence retained."""
import argparse,datetime,getpass,importlib.util,json,os,pathlib,sys
ROOT=pathlib.Path(__file__).resolve().parents[2]
def module(name,path):
 sys.path.insert(0,str(path.parent));spec=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--out',required=True);a=ap.parse_args()
 out=pathlib.Path(a.out);out.mkdir(parents=True,exist_ok=True)
 key=os.environ.get('REDFOX_API_KEY') or getpass.getpass('Redfox key (hidden): ')
 os.environ['REDFOX_API_KEY']=key
 growth=module('growth',ROOT/'xhs-follower-growth-chart/scripts/query_rankings.py')
 similar=module('similar',ROOT/'xiaohongshu-similar-account/scripts/xiaohongshu_account_recommender.py')
 jobs=[('similar-evan',{'redId':'1231177327','track':'','maxFans':'','minFans':'','level':'','source':'小红书对标账号-GitHub'}),('similar-coco',{'redId':'CocoAIGrowth','track':'','maxFans':'','minFans':'','level':'','source':'小红书对标账号-GitHub'})]+[(f'growth-{d}',{'dateType':3,'rankDate':d,'type':'学习教育','source':growth.RankingAPIClient.SOURCE}) for d in ['2026-08-01','2026-09-01','2026-10-01']]
 for name,payload in jobs:
  entry={'query_id':name,'requested':payload,'collected_at':datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=8))).isoformat()}
  try:
   if name.startswith('similar'): result=similar.call_api(payload)
   else: result=growth.HTTPSClient(timeout=25).post(growth.RankingAPIClient.API_URL,payload,{'X-API-KEY':key,'REDFOX_API_KEY':key})
   entry.update(status='response',response=result)
   data=result.get('data'); count=len(data) if isinstance(data,(list,dict)) else None
   print(name,'code',result.get('code'),'data_size',count,flush=True)
  except Exception as e:
   entry.update(status='error',error_type=type(e).__name__,error=str(e).replace(key,'[REDACTED]'))
   print(name,'error',entry['error'],flush=True)
  (out/(name+'.json')).write_text(json.dumps(entry,ensure_ascii=False,indent=2))
if __name__=='__main__': main()
