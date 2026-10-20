#!/usr/bin/env python3
"""Compute supplied editorial scores and render every source, including uncertain/unscored rows."""
import argparse
import csv
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


def calculate(topic, weights):
    if not topic.get('scope'):
        return None, None
    values = topic['scores']
    lower = sum(w * Decimal(str(v if v is not None else 0)) for w, v in zip(weights, values)) * 2
    upper = sum(w * Decimal(str(v if v is not None else 5)) for w, v in zip(weights, values)) * 2
    return tuple(float(x.quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)) for x in (lower, upper))


def score_label(t):
    if t['lower'] is None:
        return '未独立评分'
    return f"{t['total']:.1f}" if t['total'] is not None else f"{t['lower']:.1f}—{t['upper']:.1f}"


def cell(value):
    return str(value if value is not None else '未知').replace('|', '\\|').replace('\n', '<br>')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    data = json.loads(args.input.read_text(encoding='utf-8'))
    dimensions = data['dimensions']
    weights = [Decimal(str(w)) for w in data['weights']]
    if len(dimensions) != 7 or len(weights) != 7 or any(w < 0 for w in weights) or sum(weights) != 1:
        raise ValueError('Exactly seven dimensions and nonnegative weights summing to one required')
    seen = set()
    for topic in data['topics']:
        if topic['id'] in seen or not topic.get('url'):
            raise ValueError('Unique IDs and source URLs required')
        seen.add(topic['id'])
        if data.get('preserve_original_titles') and topic['title'] != topic['source_title']:
            raise ValueError('Research title must preserve source_title verbatim')
        if len(topic['scores']) != 7 or len(topic['reasons']) != 7:
            raise ValueError('Seven scores and reasons required')
        if any(v is not None and (isinstance(v, bool) or not isinstance(v, (int, float)) or not 0 <= v <= 5) for v in topic['scores']):
            raise ValueError('Score must be null or 0..5')
        topic['lower'], topic['upper'] = calculate(topic, weights)
        topic['total'] = topic['lower'] if topic['lower'] == topic['upper'] else None
    rows = data['topics']
    # Partial rankings: do not use a missing dimension's midpoint or lower bound as an actual score.
    for t in rows:
        peers = [o for o in rows if o['lane'] == t['lane'] and o['lower'] is not None and o.get('count_as_candidate', True)]
        if t['lower'] is None or not t.get('count_as_candidate', True):
            t['rank_min'] = t['rank_max'] = None
        else:
            t['rank_min'] = 1 + sum(o['lower'] > t['upper'] for o in peers)
            t['rank_max'] = len(peers) - sum(o['upper'] < t['lower'] for o in peers)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'scores.json').write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    with (args.out / 'scores.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['id','lane','original_title',*dimensions,'total','lower','upper','lane_rank_min','lane_rank_max','status','confidence','source_type','source_metrics','how_to_explain','decision_reason','preparation','source','gap',*[d+'_reason' for d in dimensions]])
        for t in rows:
            writer.writerow([t['id'],t['lane'],t['source_title'],*t['scores'],t['total'],t['lower'],t['upper'],t['rank_min'],t['rank_max'],t['status'],t['confidence'],t.get('source_type'),t.get('metrics_summary'),t['scope'],t.get('decision_reason'),t.get('preparation'),t['url'],t['gap'],*t['reasons']])
    weighted = ' / '.join(f'{d} {float(w)*100:g}%' for d,w in zip(dimensions,weights))
    candidates = [t for t in rows if t['lower'] is not None and t.get('count_as_candidate', True)]
    lines = ['# Eden 原题保留 · 双线重评', '',
             f"评分版本：{data['version']}｜证据截至：{data['as_of']}｜共{len(rows)}条来源记录，{len(candidates)}条独立方案已评，全部展示。", '',
             data.get('note',''), '',
             '各维0—5，总分0—10；权重：'+weighted+'。7.5是待校准参考线，不是合格/开工门槛。', '',
             '未知分不填2分或中点；区间是缺项从0至5的算术上下界，不是统计置信区间。线内名次范围只反映可确认的分数优势，重叠者不强分高低；表内顺序是审阅顺序。', '',
             '原题逐字保留供选题，不代表将照搬标题中的免费、收入、效率、身份、时长承诺发布。评分针对卡内写明的Eden方案；证据强度、制作准备、三月增长分开。', '']
    lanes = list(dict.fromkeys(t['lane'] for t in rows))
    for lane in lanes:
        subset = [t for t in rows if t['lane']==lane]
        lines += [f'## {lane}', '', '| ID | 原题/来源 | 原作指标快照 | HD | FIT | DIF | PRE | HOOK | COST | SEO | 新分 | 线内名次范围 | 状态 |', '|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---|---|']
        for t in subset:
            rank = str(t['rank_min']) if t['rank_min'] == t['rank_max'] and t['rank_min'] is not None else (f"{t['rank_min']}—{t['rank_max']}" if t['rank_min'] is not None else '—')
            cells = [t['id'], f"[{t['source_title']}]({t['url']})",t.get('metrics_summary',t.get('evidence','')), *[v if v is not None else '？' for v in t['scores']],score_label(t),rank,t['status']]
            lines.append('| '+' | '.join(cell(v) for v in cells)+' |')
    lines += ['', '## 怎么讲与取舍总览', '', '| ID | 原题 | Eden怎么讲 | 保留/暂缓/合并理由 |', '|---|---|---|---|']
    for t in rows:
        lines.append('| '+' | '.join(cell(v) for v in [t['id'],t['source_title'],t.get('scope') or '尚未形成独立方案；保留原题及来源。',t.get('decision_reason',t['gap'])])+' |')
    lines += ['', '## 逐条依据与制作缺口', '']
    for t in rows:
        lines += [f"### {t['id']} · {t['source_title']}", '', f"[原作链接]({t['url']})｜{t.get('source_type','来源类型见证据')}｜{t.get('author','作者见原作')}｜{t.get('published_at','日期未保存')}", '',
                  '**来源表现：** '+t.get('metrics_summary',t['evidence']), '', '**原始证据：** '+t['evidence'], '',
                  '**Eden怎么讲：** '+(t['scope'] or '未形成独立方案，不编造内容和评分。'), '',
                  '**保留与不继承：** '+t.get('retain_and_limits','见内容方案与缺口。'), '',
                  '**取舍理由：** '+t.get('decision_reason',t['gap']), '',
                  '**证据置信度：** '+t['confidence']+'。**制作准备：** '+t.get('preparation',t['gap']), '',
                  '**缺口：** '+t['gap']+'。**三个月增长：** '+t.get('growth_status','本轮未重新核验，不由原作计数推定。'), '',
                  '**新分：** '+score_label(t)+'。**原记录：** '+str(t.get('previous_total','新增/无旧总分'))+'；规则与方案可能变化，分差不是传播效果变好。', '',
                  '| 维度 | 分数 | 加权贡献 | 理由 |', '|---|---:|---:|---|']
        for dim,v,w,reason in zip(dimensions,t['scores'],weights,t['reasons']):
            contribution = f'{2*float(w)*v:.2f}' if v is not None and t.get('scope') else ('0—'+f'{10*float(w):.2f}' if t.get('scope') else '—')
            lines.append('| '+' | '.join(cell(x) for x in [dim,v,contribution,reason])+' |')
        for path in t.get('evidence_paths',[]):
            lines.append(f"\n证据文件：[{Path(path).name}]({Path(path).resolve()})")
    lines += ['', '## 时效、关联与待验证假设', '', '具体假设是编辑预期，需发布后验证；不预设命中门槛。素材和未明确方案不编造假设。', '', '| ID | 时效与依据 | 关联对标 | 具体假设 | 观察线索 |', '|---|---|---|---|---|']
    for t in rows:
        lib=t.get('library') or {}
        lines.append('| '+' | '.join(cell(v) for v in [t['id'],str(lib.get('时效类型','待验证'))+'；'+str(lib.get('时效判断依据','待补')), '、'.join(lib.get('关联对标',[])) or '待验证', lib.get('具体假设','待补：按本轮内容方案明确') if t.get('scope') else '待明确内容方案', lib.get('假设观察线索','待补') if t.get('scope') else '随主方案或待明确后复盘'])+' |')
    lines += ['', '## 人工选择', '', '填写选用/暂缓/不用及理由；空白表示尚未选择。评分和建议均不代替用户决定。']
    (args.out / '全量选题评分.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({'visible_records':len(rows),'independent_candidates_scored':len(candidates),'complete_totals':sum(t['total'] is not None for t in rows),'interval_scores':sum(t['lower'] is not None and t['total'] is None for t in rows)},ensure_ascii=False))


if __name__ == '__main__':
    main()
