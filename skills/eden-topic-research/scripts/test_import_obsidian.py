"""Run in isolated temporary vaults; never modify the real library."""
import copy, hashlib, json, pathlib, subprocess, sys, tempfile, unittest

SCRIPT=pathlib.Path(__file__).with_name('import_obsidian.py')

def topic(url='https://www.xiaohongshu.com/explore/1234567890abcdef12345678'):
    return {'id':'K01','source_title':'测试原题','lane':'宝妈科普型','url':url,
            'scope':'解释概念并展示检查环节','lower':7.0,'upper':8.0,'scores':[4,4,4,4,4,4,None],
            'reasons':['已有来源与方案']*7,'confidence':'待验证','status':'保留候选','gap':'原视频待验证',
            'evidence':'测试来源','author':'测试作者','library':{
                '目标':'本轮新目标，不沿用旧K01','目标格式':'图解（建议）','时效类型':'常青科普',
                '时效判断依据':'基础知识，不证明当前热度','关联对标':['[[Eden账号运营/对标账号库/测试作者]]'],
                '具体假设':'观众能指出一个检查步骤','假设观察线索':'记录观众复述与误解'}}

def payload(rows):
    return {'version':'test-v0.8','research_date':'2026-10-20','as_of':'测试存档', 'positioning_version':'V0.3',
            'dimensions':['HD','FIT','DIF','PRE','HOOK','COST','SEO'],
            'weights':[.2,.3,.1,.15,.1,.1,.05], 'topics':rows}

def snapshot(folder):
    return {str(f.relative_to(folder)):hashlib.sha256(f.read_bytes()).hexdigest() for f in folder.rglob('*') if f.is_file()}

def props(path):
    return dict((json.loads(k),json.loads(v)) for line in path.read_text().split('---',2)[1].splitlines() if ': ' in line for k,v in [line.split(': ',1)] if k not in ['"添加日期"','"研究日期"'])

class ImportTest(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=pathlib.Path(self.tmp.name);self.vault=self.root/'vault';self.dest=self.vault/'Eden账号运营/选题库'
        self.input=self.root/'scores.json'
        p=self.vault/'Eden账号运营/对标账号库/测试作者.md';p.parent.mkdir(parents=True);p.write_text('# 测试作者')
    def run_import(self,data,date='2026-10-20',ok=True):
        self.input.write_text(json.dumps(data,ensure_ascii=False))
        r=subprocess.run([sys.executable,str(SCRIPT),'--input',str(self.input),'--vault',str(self.vault),'--added-date',date],capture_output=True,text=True)
        if ok:self.assertEqual(r.returncode,0,r.stderr);return json.loads(r.stdout)
        self.assertNotEqual(r.returncode,0);return r.stderr
    def test_user_choice_review_rename_and_url_variants_preserved(self):
        data=payload([topic()]);self.run_import(data)
        path=next((self.dest/'选题卡片').glob('*.md'))
        text=path.read_text().replace('"你的选择": null','你的选择: 选用').replace('"状态": "待选"','状态: 已发布').replace('"实际命中结果": null','实际命中结果: 部分命中').replace('"原作点赞": null','原作点赞: 123')+'\n## 我自己的复盘\n观众的问题需要重新解释。\n'
        path.write_text(text);renamed=path.with_name('我的自定义卡名.md');path.rename(renamed)
        initial=snapshot(self.dest)
        changed=copy.deepcopy(data);changed['topics'][0]['url']='https://www.xiaohongshu.com/discovery/item/1234567890abcdef12345678?xsec_token=example'
        changed['topics'][0]['library']['具体假设']='重评的新假设';changed['topics'][0]['lower']=8.5
        out=self.run_import(changed,date='2026-10-21')
        self.assertEqual((out['created'],out['skipped']),(0,1))
        for f,digest in initial.items():self.assertEqual(snapshot(self.dest)[f],digest,f)
        self.assertEqual(len(list((self.dest/'选题卡片').glob('*.md'))),1)
        self.assertEqual(len(list((self.dest/'资料与规则/批次').iterdir())),2)
    def test_new_fields_dates_repeat_and_same_title_different_source(self):
        t=topic();dup=copy.deepcopy(t);dup['id']='K02';dup['url']+='?from=test'
        data=payload([t,dup]);out=self.run_import(data)
        self.assertEqual((out['created'],out['skipped']),(1,1))
        first=next((self.dest/'选题卡片').glob('*.md'));d=props(first)
        self.assertEqual(d['目标'],'本轮新目标，不沿用旧K01')
        for key in ['具体假设','关联对标','复盘观察窗口','复盘比较基线','观众理解反馈','受众自述反馈','新增关注','观看留存记录']:self.assertIn(key,d)
        self.assertIsNone(d['实际命中结果']);self.assertEqual(d['三个月增长'],'待验证')
        self.assertIn('"研究日期": 2026-10-20',first.read_text())
        self.assertNotIn('2026-10-19',first.read_text())
        initial=snapshot(self.dest);self.run_import(data);self.assertEqual(initial,snapshot(self.dest))
        other=topic('https://www.xiaohongshu.com/explore/aaaaaaaaaaaaaaaaaaaaaaaa')
        self.run_import(payload([other]));self.assertEqual(len(list((self.dest/'选题卡片').glob('*.md'))),2)
        self.assertEqual(len(list((self.dest/'资料与规则/批次').iterdir())),2)
        self.assertEqual(snapshot(self.dest)[str(first.relative_to(self.dest))],initial[str(first.relative_to(self.dest))])
    def test_missing_metadata_rejects_whole_batch_before_write(self):
        bad=topic('https://www.xiaohongshu.com/explore/aaaaaaaaaaaaaaaaaaaaaaaa');del bad['library']['具体假设']
        error=self.run_import(payload([topic(),bad]),ok=False)
        self.assertIn('具体假设',error);self.assertFalse(self.dest.exists())
    def test_hot_without_evidence_and_missing_link_rejected(self):
        t=topic();t['library']['时效类型']='近期热点'
        self.assertIn('current_heat_evidence',self.run_import(payload([t]),ok=False))
        t=topic();t['library']['关联对标']=['[[不存在]]']
        self.assertIn('目标不存在',self.run_import(payload([t]),ok=False))
        self.assertFalse(self.dest.exists())
    def test_unscored_state_explicit_not_inherited_from_id(self):
        t=topic();t['scope']='';t['lower']=t['upper']=None;t['library_state']='素材备查'
        del t['library']['具体假设'];del t['library']['假设观察线索']
        self.run_import(payload([t]));d=props(next((self.dest/'选题卡片').glob('*.md')))
        self.assertEqual(d['状态'],'素材备查');self.assertEqual(d['假设状态'],'待明确内容方案')
        self.assertIn('待明确',d['具体假设'])

if __name__=='__main__':unittest.main()
