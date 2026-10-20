#!/usr/bin/env python3
"""Create Obsidian topic cards and a native Bases board. Existing notes/views are never overwritten."""
import argparse, datetime, hashlib, json, pathlib, re
from urllib.parse import urlsplit, parse_qs
from zoneinfo import ZoneInfo

def frontmatter(values):
    lines=['---']
    for k,v in values.items():
        val=json.dumps(v,ensure_ascii=False)
        if k in ['添加日期','研究日期'] and isinstance(v,str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}',v):val=v
        lines.append(json.dumps(k,ensure_ascii=False)+': '+val)
    return '\n'.join(lines+['---',''])

def numeric(value):
    if isinstance(value,(int,float)):return value
    if isinstance(value,str):
        m=re.fullmatch(r'([0-9.]+)万',value)
        if m:return float(m[1])*10000
    return None

def newfile(path,text):
    if path.exists():return False
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x',encoding='utf-8') as f:f.write(text)
    return True

def source_identity(url):
    """Only collapse known platform URL variants; keep opaque short links intact."""
    u=urlsplit(url);host=(u.hostname or '').lower()
    if host in ('xiaohongshu.com','www.xiaohongshu.com'):
        m=re.search(r'/(?:explore|discovery/item)/([0-9a-fA-F]{24})(?:/|$)',u.path)
        if m:return 'xhs:'+m[1].lower()
    if host in ('youtube.com','www.youtube.com','m.youtube.com'):
        vid=parse_qs(u.query).get('v',[None])[0]
        if u.path=='/watch' and vid:return 'youtube:'+vid
    if host=='youtu.be' and u.path.strip('/'):return 'youtube:'+u.path.strip('/')
    return url


def scalar(header, name):
    # Read only identity scalars; never deserialize or rewrite user-owned YAML.
    m=re.search(r'^'+r'["\']?'+re.escape(name)+r'["\']?:[ \t]*(.*)$',header,re.M)
    if not m:return None
    value=m[1].strip()
    if value.startswith('"'):
        try:return json.loads(value)
        except ValueError:return None
    return value.strip("'") or None


def validate_library(t, vault):
    lib=t.get('library') or {}
    required=['目标','目标格式','时效类型','时效判断依据']
    if t['lower'] is not None:required+=['具体假设','假设观察线索']
    for k in required:
        if not isinstance(lib.get(k),str) or not lib[k].strip():
            raise ValueError(f"{t['id']}: 缺少 library.{k}；先根据本轮内容方案补齐")
    if lib['时效类型'] not in ('常青科普','历史案例','近期热点','待验证'):
        raise ValueError('时效类型必须沿用现有枚举')
    if lib['时效类型']=='近期热点' and not t.get('current_heat_evidence'):
        raise ValueError('近期热点需要 current_heat_evidence，当下升温证据不能由发布日期代替')
    links=lib.get('关联对标')
    if not isinstance(links,list):raise ValueError('library.关联对标 必须为链接列表；待验证时可用空列表')
    for link in links:
        if not isinstance(link,str) or not link.startswith('[[') or not link.endswith(']]'):
            raise ValueError('关联对标必须使用现有Obsidian内部链接')
        target=link[2:-2].split('|')[0].split('#')[0]
        path=vault/target
        if not (path.is_file() or pathlib.Path(str(path)+'.md').is_file()):
            raise ValueError('关联对标目标不存在：'+target)
    if t['lower'] is None and t.get('library_state') not in ('待补内容','合并参考','素材备查'):
        raise ValueError('未评分来源须明确 library_state，不按旧批次编号推断')
    return lib


def main():
    p=argparse.ArgumentParser();p.add_argument('--input',type=pathlib.Path,required=True);p.add_argument('--vault',type=pathlib.Path,required=True);p.add_argument('--folder',default='Eden账号运营/选题库');p.add_argument('--added-date',default=datetime.datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat());a=p.parse_args()
    datetime.date.fromisoformat(a.added_date)
    raw=a.input.read_text();data=json.loads(raw);topics=data['topics'];rel=a.folder;dest=a.vault/rel;cards=dest/'选题卡片';meta=dest/'资料与规则'
    if not dest.resolve().is_relative_to(a.vault.resolve()):raise ValueError('选题库必须位于指定vault内')
    research_date=data.get('research_date')
    existing={};identities={};conflicts=[]
    for f in cards.glob('*.md'):
        parts=f.read_text().split('---',2)
        if len(parts)<3:raise ValueError('已有卡缺少身份属性，先人工核对：'+str(f))
        key=scalar(parts[1],'选题键');url=scalar(parts[1],'参考视频')
        if not key and not url:raise ValueError('已有卡的选题键与参考视频均缺失，先人工核对：'+str(f))
        if key:
            if key in existing:conflicts.append(key)
            existing[key]=f
        if url:
            identity=source_identity(url)
            if identity in identities:conflicts.append(identity)
            identities[identity]=f
    if conflicts:raise ValueError('现有库含重复作品，需先核对，未执行写入：'+str(conflicts))
    # Validate all NEW records before writing any notes; old records remain opaque.
    seen=set()
    for t in topics:
        if not re.fullmatch(r'[A-Za-z0-9_-]+',t['id']):raise ValueError('选题ID仅使用字母、数字、下划线或短横线')
        identity=source_identity(t['url']);key=hashlib.sha256(t['url'].encode()).hexdigest()[:20]
        if identity in identities or key in existing or identity in seen:continue
        seen.add(identity)
        if not research_date:raise ValueError('新卡片需要本轮 research_date (YYYY-MM-DD)')
        datetime.date.fromisoformat(research_date)
        validate_library(t,a.vault)
    batch_name=a.added_date+'_'+hashlib.sha256(raw.encode()).hexdigest()[:12]
    batch_rel=rel+'/资料与规则/批次/'+batch_name
    batch=meta/'批次'/batch_name
    cards.mkdir(parents=True,exist_ok=True);meta.mkdir(exist_ok=True)
    dimnames=['需求','定位契合','差异化','传播先例','钩子潜力','制作可行性','搜索长尾']
    cards_map={};created=[];skipped=[];snapshots={}
    for i,t in enumerate(topics,1):
        key=hashlib.sha256(t['url'].encode()).hexdigest()[:20]
        title=t['source_title'];stem=t['id']+' '+re.sub(r'[\\/:*?"<>|\[\]#^]','＿',title).strip()[:100]
        identity=source_identity(t['url'])
        f=identities.get(identity) or existing.get(key)
        o=t.get('primary_observation') or {}
        snapshots[t['id']]={'url':t['url'],'source_title':title,'primary_observation':{k:v for k,v in o.items() if k not in ['raw','body']},'observations':[{k:v for k,v in ob.items() if k not in ['raw','body']} for ob in t.get('source_observations',[])]}
        if f:
            cards_map[t['id']]=str(f.relative_to(a.vault));skipped.append(t['id']);continue
        f=cards/(stem+'.md')
        if f.exists():f=cards/(stem+' '+key+'.md')
        if f.exists():raise ValueError('目标文件冲突，未覆盖：'+str(f))
        cards_map[t['id']]=str(f.relative_to(a.vault))
        lib=t['library']
        scored=t['lower'] is not None
        state='待选' if scored else t['library_state']
        result=(f"{t['lower']:.1f}–{t['upper']:.1f} / 10" if t['lower']!=t['upper'] else f"{t['lower']:.1f} / 10") if scored else '未独立评分'
        prediction='达到7.5参考线，待验证' if scored and t['lower']>=7.5 else '跨7.5参考线，待补证' if scored and t['upper']>=7.5 else '低于参考线，仍可选择' if scored else '内容待明确／素材不预测'
        hits=[name for name,v in zip(dimnames,t['scores']) if v is not None and v>=4] if scored else []
        o=t.get('primary_observation') or {};m=o.get('metrics',{})
        # All primary metrics are from ONE observation. Never mix sources into an apparent single timestamp.
        goals,fmt=lib['目标'],lib['目标格式']
        props={
          '选题ID':t['id'],'选题键':key,'原题':title,'内容线':t['lane'],'状态':state,
          '条目类型':'内容候选' if scored else '来源参考','审阅顺序':i,'添加日期':a.added_date,'研究日期':research_date,
          '目标':goals,'目标格式':fmt,'参考视频':t['url'],'原作作者':t.get('author'),
          '原作发布时间':t.get('published_at'),'来源类型':t.get('source_type'),'原作数据':t.get('metrics_summary'),
          '原作点赞':numeric(m.get('likedCount')),'原作收藏':numeric(m.get('collectedCount')),'原作评论':numeric(m.get('commentsCount')),
          '原作分享':numeric(m.get('sharedCount')),'原作播放':numeric(m.get('viewCount')),'粉丝快照':numeric(m.get('authorFans')),
          '指标精度':'点赞为约数；其余以来源记录为准' if isinstance(m.get('likedCount'),str) else '按来源保存；未知字段留空',
          '评分结果':result,'评分下限':t['lower'],'评分上限':t['upper'],
          **{dim:v for dim,v in zip(data['dimensions'],t['scores'])},
          '预期命中':hits,'预测判断':prediction,'预测验证':'待发布验证','实际命中结果':None,
          '证据置信度':t['confidence'],'评分版本':data['version'],'同题组':t.get('cluster_id',t['id']),
          '独立选题计数':t.get('count_as_candidate',True),'三个月增长':'待验证','你的选择':None,
          '计划发布日期':None,'发布链接':None,'实际发布日期':None,'复盘日期':None,
          '实际播放':None,'实际点赞':None,'实际收藏':None,'实际评论':None,
          '时效类型':lib['时效类型'],'时效判断依据':lib['时效判断依据'],'关联对标':lib['关联对标'],
          '具体假设':lib['具体假设'] if scored else '待明确内容方案后补充；不编造观众收获假设。',
          '假设状态':'待验证' if scored else '待明确内容方案',
          '假设观察线索':lib['假设观察线索'] if scored else '内容明确后再确定；合并参考随主方案复盘。',
          '假设更新日期':research_date,'核验状态':'待验证（具体缺口见卡片正文）',
          '复盘观察窗口':None,'复盘比较基线':None,'观众理解反馈':None,'受众自述反馈':None,
          '新增关注':None,'观看留存记录':None,
          'tags':['Eden选题库','待人工选择']}
        body=[f'# {title}','',f'[[{rel}/选题看板.base|← 返回选题看板]] · [参考视频／原文]({t["url"]})','',
              '> 入库表示收进候选库，当前尚未选定制作。原题中的身份、免费、金额、效果或时长是来源标题表述，不自动成为Eden承诺。','',
              '## 内容目标与讲法','',f'**目标：** {goals}。**建议形式：** {fmt}。','',t.get('scope') or '当前未形成独立方案，保留来源供进一步判断。','',
              '**保留与不继承：** '+t.get('retain_and_limits','见取舍理由。'),'',
              '## 评分与预期命中','',f'**评分结果：{result}**。{prediction}。','',
              '**预期命中项：** '+('、'.join(hits) if hits else '暂无已支持的强项')+'。这里指七维中当前编辑评分≥4的强项，不是发布后已经命中，也不是爆款概率。','',
              '缺项区间由未知维度0—5的上下界计算，不是统计置信区间；7.5为待校准参考线。','',
              '| 维度 | 得分／5 | 权重 | 判断依据 |','|---|---:|---:|---|']
        for dim,val,w,reason in zip(data['dimensions'],t['scores'],data['weights'],t['reasons']):
            body.append('| '+ ' | '.join([dim,str(val) if val is not None else '未知',f'{w*100:g}%',reason.replace('|','\\|')])+' |')
        body+=['','## 取舍与制作准备','', '**当前评审：** '+t['status'],'','**取舍理由：** '+t.get('decision_reason',t['gap']),'','**制作准备：** '+t.get('preparation',t['gap']),'','**证据缺口：** '+t['gap'],'','## 参考来源与数据','',f'- 原题：{title}',f'- 作者：{t.get("author","未知")}',f'- 原链接：[打开参考作品]({t["url"]})',f'- 发布时间原记录：{t.get("published_at","未知")}',f'- 来源类型：{t.get("source_type","未知")}',f'- 指标快照：{t.get("metrics_summary","未知")}',f'- 阅读范围与依据：{t["evidence"]}',f'- 证据置信度：{t["confidence"]}', f'- 数据口径：{data.get("as_of","见来源快照")}。研究日期不替代数据采集日期；粉丝快照不代表发布时粉丝。', '- 三个月持续增长：待验证；当前累计点赞不能作为增长曲线。','',
          '## 时效、对标与具体假设','',
          '**时效类型：** '+props['时效类型']+'。'+props['时效判断依据'],
          '**关联对标：** '+('、'.join(props['关联对标']) or '待验证、待补；不猜测账号关联'),
          '**具体假设：** '+props['具体假设'],
          '**观察线索：** '+props['假设观察线索'],
          '**证据状态：** 待验证。编辑假设不是已验证的家长需求或效果。',
          '**当前升温依据：** '+str(t.get('current_heat_evidence') or '待验证；不由发布时间和累计赞藏推断'),'',
          '## 选择与发布后复盘','',
          '不预设命中门槛；7.5评分参考线与≥4评分强项均不构成效果验收线。','',
          '| 记录项 | 本次记录 |','|---|---|',
          '| 采用内容与假设调整 | 待选用后确认 |',
          '| 观察窗口及采集时间 | 待发布后填写 |',
          '| 账号比较基线 | 待积累；不足标基线不足 |',
          '| 观看、收藏、评论、关注、留存 | 按平台实际可得数据填写；未知留空 |',
          '| 观众理解证据与受众自述 | 待验证，保留具体反馈来源 |',
          '| 支持与不支持假设的证据 | 待验证 |',
          '| 实际命中判断与理由 | 待验证；证据不足不强判成败 |',
          '| 下次调整 | 待复盘 |','', 
          '- 你的选择：在属性中填“选用／暂缓／不用”，补充理由。', '- 状态建议：待选 → 已选 → 制作中 → 已发布 → 已复盘；未确认采用前保持待选。', '- 发布前：记录本条希望命中的目标、观察指标与比较基线。', '- 发布后：填写发布链接、日期与同龄窗口数据，再判断“实际命中结果”。没有自有基线时记录“基线不足”，不硬判成败。', '',
          '| 预期 | 发布后证据 | 是否命中 | 复盘说明 |','|---|---|---|---|', f'| {goals} | 待发布后填写 | 待验证 | |','',
          '## 用户补充','', '选择理由：','', '希望调整的讲法：','',
          f'评审依据：[[{rel}/资料与规则/评分规则|评分规则]] · [[{batch_rel}/入库批次|入库批次说明]]','']
        text=frontmatter(props)+'\n'+'\n'.join(body)
        if key in existing or f.exists():skipped.append(t['id'])
        elif newfile(f,text):
            created.append(t['id']);identities[identity]=f;existing[key]=f
    order=['formula.选题','formula.参考','时效类型','关联对标','目标','具体假设','目标格式','note.添加日期','note.评分结果','note.预期命中','formula.复盘结果','note.原作数据']
    def view(name,filters=None,kind='cards'):
        v={'type':kind,'name':name,'order':order.copy(),'sort':[{'property':'note.审阅顺序','direction':'ASC'}]}
        if kind=='cards':v['cardSize']=320
        if filters:v['filters']={'and':filters}
        return v
    allview=view('全量看板');allview['groupBy']={'property':'note.状态','direction':'ASC'}
    pending=view('待选看板',['note["状态"] == "待选"']);pending['groupBy']={'property':'note.内容线','direction':'ASC'}
    sci=view('宝妈科普型',['note["内容线"] == "宝妈科普型"'])
    hot=view('AI育儿热点话题',['note["内容线"] == "AI育儿热点话题"'])
    viral=view('万赞参考',['note["原作点赞"] >= 10000'])
    table=view('数据总表',kind='table');table['order']=['formula.选题','note.选题ID','note.状态','note.内容线','时效类型','关联对标','具体假设','假设状态','核验状态','复盘观察窗口','复盘比较基线','note.目标','note.添加日期','note.评分结果','note.预期命中','note.预测判断','note.预测验证','formula.参考','note.原作作者','note.原作点赞','note.原作收藏','note.粉丝快照',*['note.'+d for d in data['dimensions']],'note.你的选择','note.发布链接','note.实际命中结果']
    board={'filters':{'and':[f'file.inFolder("{rel}/选题卡片")','file.ext == "md"']},'formulas':{'选题':'file.asLink(note["原题"])','参考':'link(note["参考视频"], "打开参考视频 ↗")','复盘结果':'if(note["实际命中结果"], note["实际命中结果"], note["预测验证"])'},'properties':{'formula.选题':{'displayName':'选题原题'},'formula.参考':{'displayName':'参考视频'},'note.预期命中':{'displayName':'预期命中项'},'formula.复盘结果':{'displayName':'实际命中结果'}},'views':[allview,pending,sci,hot,viral,table]}
    for v in board['views']:
        v['order']=[x.removeprefix('note.') for x in v['order']]
        v['sort'][0]['property']='审阅顺序'
        if 'groupBy' in v:v['groupBy']['property']=v['groupBy']['property'].removeprefix('note.')
    newfile(dest/'选题看板.base',json.dumps(board,ensure_ascii=False,indent=2)+'\n')
    home=['# Eden 选题库','',f'[[{rel}/选题看板.base|打开完整选题看板 ↗]] · [[{rel}/资料与规则/字段说明|字段与使用说明]]','',
          f'首批归档{len(topics)}条输入；新增{len(created)}张卡、复用{len(skipped)}条已有来源。入库不等于选用，低分、待核和素材保留；当前数量看实时看板。','',
          '看板可切换：全量看板、待选看板、宝妈科普型、AI育儿热点话题、万赞参考、数据总表。点击卡片标题查看完整讲法、七维理由与原视频链接。','',
          '“预期命中”表示当前方案的评分强项；“预测验证／实际命中结果”须发布后复盘。目前全部待验证。','',
          f'![[{rel}/选题看板.base#全量看板]]','', '## 选题索引','']
    for t in topics:home.append(f'- [[{cards_map[t["id"]][:-3]}|{t["id"]} · {t["source_title"]}]]')
    newfile(dest/'00_选题库入口.md','\n'.join(home)+'\n')
    rule=pathlib.Path(__file__).resolve().parents[1]/'references/scoring.md'
    newfile(meta/'评分规则.md',rule.read_text().replace('(recall-and-provenance.md)','(召回与来源核验.md)'))
    recall=rule.parent/'recall-and-provenance.md';newfile(meta/'召回与来源核验.md',recall.read_text())
    newfile(meta/'字段说明.md',(rule.parent/'library-fields.md').read_text())
    report=[f'# {a.added_date} 入库批次','',f'- 输入{len(topics)}条；新增{len(created)}张，保留已有{len(skipped)}条。',f'- 研究日期：{research_date or "旧批次复用，见评分输入"}；证据口径：{data.get("as_of","待验证")}。',f'- 评分版本：{data["version"]}；定位版本：{data.get("positioning_version","待记录")}。','- 不预设命中门槛；来源快照和本次重评不覆盖已有卡片、人工选择或复盘。','- 已有卡的最新研究存入本批评分输入.json；应用重评须另存评分历史并核对字段差异。','', '## 本批选题链接','']
    report += [f'- [[{cards_map[t["id"]][:-3]}|{t["id"]} · {t["source_title"]}]]' for t in topics]
    newfile(batch/'入库批次.md','\n'.join(report)+'\n')
    newfile(batch/'来源快照.json',json.dumps(snapshots,ensure_ascii=False,indent=2))
    archival={k:v for k,v in data.items() if k!='topics'};archival['topics']=[{k:v for k,v in t.items() if k not in ['source_observations','primary_observation']} for t in topics]
    newfile(batch/'评分输入.json',json.dumps(archival,ensure_ascii=False,indent=2))
    result={'created':created,'skipped':skipped,'card_paths':cards_map,'board_path':str(dest/'选题看板.base'),'vault':str(a.vault)}
    (a.input.parent/'obsidian_import_result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
    print(json.dumps({'created':len(created),'skipped':len(skipped),'board':result['board_path']},ensure_ascii=False))

if __name__=='__main__':main()
