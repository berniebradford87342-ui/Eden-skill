#!/usr/bin/env python3
"""Normalize a bounded Redfox run without scoring, rewriting titles, or merging metrics."""
import argparse, datetime, json, pathlib
from collections import Counter
TZ=datetime.timezone(datetime.timedelta(hours=8))
def main():
 p=argparse.ArgumentParser();p.add_argument('run_dir');a=p.parse_args();root=pathlib.Path(a.run_dir)
 observations=[];queries=[]
 for folder in ('curl实测','采集'):
  for f in sorted((root/folder).glob('*.json')):
   env=json.loads(f.read_text());response=env.get('response',{});data=response.get('data');request=env.get('payload',env.get('requested',{}))
   q={'query_id':env['query_id'],'request':request,'response_code':response.get('code'),'status':env.get('status'),'collected_at':env.get('collected_at'),'evidence_path':str(f.relative_to(root))}
   if isinstance(data,dict) and 'articles' in data:
    rows=data['articles'];q['returned_rows']=len(rows);q['server_total']=data.get('total')
    for v in rows:
     observations.append(dict(platform='xiaohongshu',source_id='xhs:'+v['id'],title=v.get('title') or None,author=v.get('authorNickname'),author_id=v.get('authorId'),author_followers_snapshot=v.get('authorFans'),author_followers_as_of=None,author_followers_note='第三方返回快照；计数时点未知，非发布时粉丝数',source_type='keyword_search' if request.get('keyword') else 'search_endpoint_unspecified',published_at=v.get('createTime'),url=v.get('shareInfoLink'),body=v.get('desc'),verification='第三方正文；未默认读完视频',provider='redfox',collected_at=env['collected_at'],updated_at=None,query_id=env['query_id'],evidence_path=str(f.relative_to(root)),metrics={k:v.get(k) for k in ('likedCount','collectedCount','commentsCount','sharedCount')},commercial_status='待内容核对'))
   elif isinstance(data,dict) and 'opusInfoList' in data:
    rows=data['opusInfoList'];q['returned_rows']=len(rows);q['reported_pages']=data.get('pages')
    for v in rows:
     date=datetime.datetime.fromtimestamp(v['publishTime'],TZ).isoformat() if v.get('publishTime') else None
     observations.append(dict(platform='bilibili',source_id='bili:'+v['bvId'],title=v.get('title'),author=v.get('nickname'),published_at=date,url=v.get('url'),body=v.get('description'),verification='第三方标题/简介；未默认读完视频',provider='redfox',collected_at=env['collected_at'],updated_at=None,query_id=env['query_id'],evidence_path=str(f.relative_to(root)),metrics={k:v.get(k) for k in ('viewNum','likeNum','collectNum','commentNum')},commercial_status='待内容核对'))
   elif isinstance(data,list):
    q['returned_rows']=len(data);q['actual_periods']=sorted({(v.get('rankDate'),v.get('rankPeriod'),v.get('dataFetchTime')) for v in data})
   elif isinstance(data,dict):q['data_fields']=list(data)
   queries.append(q)
 ui=root/'ui_observations.json'
 if ui.exists():observations.extend(json.loads(ui.read_text()))
 sources={}
 for v in observations:
  key=v['source_id'];r=sources.setdefault(key,{'source_id':key,'platform':v['platform'],'url':v['url'],'observations':[]});r['observations'].append(v)
 def lines(path,items):path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in items))
 lines(root/'sources.jsonl',sources.values());lines(root/'snapshots.jsonl',observations)
 summary={'query_count':len(queries),'response_codes':dict(Counter(str(x['response_code']) for x in queries)),'raw_api_work_rows':sum(q.get('returned_rows',0) for q in queries if q['query_id'].startswith(('xhs','bili'))),'api_work_rows_by_platform':{prefix:sum(q.get('returned_rows',0) for q in queries if q['query_id'].startswith(prefix)) for prefix in ('xhs','bili')},'unique_api_works_by_platform':{prefix:len({v['source_id'] for v in observations if v.get('provider')=='redfox' and v['source_id'].startswith(prefix+':')}) for prefix in ('xhs','bili')},'unique_sources_including_manual':len(sources),'snapshot_rows':len(observations),'queries':queries}
 (root/'collection_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in summary.items() if k!='queries'},ensure_ascii=False))
if __name__=='__main__':main()
