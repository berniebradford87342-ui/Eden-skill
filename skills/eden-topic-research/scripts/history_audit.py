#!/usr/bin/env python3
"""Audit saved Redfox monthly boards and dated article queries; no network calls.

Config paths are relative to the config file. Missing rank entries remain null.
The result proves coverage/observations, never audience fit or topic causality.
"""
import argparse
import csv
import json
import re
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def number(raw):
    if raw is None or isinstance(raw, bool):
        return None
    match = re.fullmatch(r'([+-]?\d+(?:\.\d+)?)([w万]?)', str(raw).replace(',', '').strip())
    return float(Decimal(match[1]) * (10000 if match[2] else 1)) if match else None


def profile_id(url):
    match = re.search(r'/user/profile/([a-zA-Z0-9]+)', url or '')
    return match[1] if match else None


def verdict(cells):
    values = [c['fans_growth'] for c in cells]
    if len(values) != 3 or any(v is None for v in values):
        return 'insufficient_evidence'
    return 'three_positive_months' if all(v > 0 for v in values) else 'not_three_positive_months'


def audit(config, base):
    periods = config['months']
    dates = [date.fromisoformat(m + '-01') for m in periods]
    serial = [d.year * 12 + d.month for d in dates]
    if len(serial) != 3 or serial != list(range(serial[0], serial[0] + 3)):
        raise ValueError('months must be three consecutive calendar months')
    boards, articles, errors = [], [], []
    panel = defaultdict(list)
    for rel in config['board_files']:
        doc = read(base / rel)
        payload = doc.get('payload', doc.get('requested', {}))
        response = doc.get('response', {})
        rows = response.get('data', [])
        if response.get('code') != 2000 or not isinstance(rows, list):
            errors.append({'file': rel, 'error': 'unsuccessful board response'})
            continue
        accepted = 0
        for row in rows:
            month = str(row.get('rankDate', ''))[:7]
            pid = profile_id(row.get('accountLink'))
            if (row.get('rankPeriod') != '月榜' or month not in periods
                    or row.get('rankDate') != payload.get('rankDate') or not pid):
                errors.append({'file': rel, 'error': 'invalid period or identity', 'row': row})
                continue
            panel[(pid, month)].append({'source_file': rel, **row})
            accepted += 1
        boards.append({'file': rel, 'requested': payload, 'returned': len(rows), 'accepted': accepted})

    def cells_for(pid):
        cells = []
        for month in periods:
            observations = panel.get((pid, month), []) if pid else []
            values = [number(r.get('fansGrowth')) for r in observations]
            distinct = set(values)
            valid = bool(values) and None not in distinct and len(distinct) == 1
            cells.append({'month': month, 'fans_growth': values[0] if valid else None,
                          'status': 'observed' if valid else ('conflict_or_unknown' if observations else 'not_observed'),
                          'approximate': any(re.search('[w万]', str(r.get('fansGrowth'))) for r in observations),
                          'evidence': observations})
        return cells

    targets = []
    for target in config['targets']:
        cells = cells_for(target.get('profile_id'))
        targets.append({**target, 'months': cells, 'growth_verdict': verdict(cells),
                        'identity_status': 'resolved' if target.get('profile_id') else 'needs_profile_id'})
    all_panel = []
    for pid in sorted({k[0] for k in panel}):
        cells = cells_for(pid)
        names = sorted({r['accountName'] for c in cells for r in c['evidence']})
        all_panel.append({'profile_id': pid, 'names': names, 'months': cells, 'growth_verdict': verdict(cells)})

    coverage = []
    for rel in config['article_files']:
        doc = read(base / rel)
        payload = doc.get('payload', doc.get('requested', {}))
        response = doc.get('response', {})
        data = response.get('data', {})
        if response.get('code') != 2000 or not isinstance(data, dict):
            errors.append({'file': rel, 'error': 'unsuccessful article response'})
            continue
        start, end = date.fromisoformat(payload['startDate']), date.fromisoformat(payload['endDate'])
        accepted, excluded = [], []
        for row in data.get('articles', []):
            try:
                published = date.fromisoformat(str(row.get('createTime', ''))[:10])
            except ValueError:
                published = None
            ok = bool(published and start <= published <= end and row.get('id'))
            record = {'source_file': rel, 'keyword': payload['keyword'], 'window_start': str(start),
                      'window_end': str(end), 'collected_at': doc.get('collected_at'),
                      'in_requested_window': ok, 'raw': row}
            (accepted if ok else excluded).append(record)
            articles.append(record)
        coverage.append({'file': rel, 'keyword': payload['keyword'], 'start': str(start), 'end': str(end),
                         'returned': len(accepted) + len(excluded), 'accepted': len(accepted),
                         'excluded': len(excluded), 'server_total': data.get('total'),
                         'earliest': min((r['raw']['createTime'] for r in accepted), default=None),
                         'latest': max((r['raw']['createTime'] for r in accepted), default=None),
                         'fallback_excluded': len(data.get('latestHotArticles') or []),
                         'coverage': 'retrieved_sample_only'})
    for target in targets:
        target['article_samples'] = [{'id': r['raw']['id'], 'title': r['raw']['title'],
                                     'published_at': r['raw']['createTime'], 'source_file': r['source_file']}
                                    for r in articles if r['in_requested_window'] and target.get('profile_id')
                                    and r['raw'].get('authorId') == target['profile_id']]
    return {'months': periods, 'boards': boards, 'targets': targets, 'all_accounts': all_panel,
            'article_coverage': coverage, 'articles': articles, 'errors': errors,
            'limits': ['Calendar months are not rolling 90 days.', 'Absence from sampled boards is not zero growth.',
                       'Current article metrics and authorFans do not prove historical growth.',
                       'Three positive months do not prove acceleration, weekly consistency, or topic causality.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', required=True, type=Path)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args()
    result = audit(read(args.config), args.config.resolve().parent)
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / 'history_audit.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    with (args.out / 'target_growth.csv').open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerow(['account', 'profile_id', *result['months'], 'verdict'])
        for row in result['targets']:
            writer.writerow([row['name'], row.get('profile_id'), *[c['fans_growth'] for c in row['months']], row['growth_verdict']])
    print(json.dumps({'board_rows': sum(x['accepted'] for x in result['boards']),
                      'unique_accounts': len(result['all_accounts']),
                      'targets_with_three_positive_months': sum(t['growth_verdict'] == 'three_positive_months' for t in result['targets']),
                      'article_rows': len(result['articles']), 'errors': len(result['errors'])}, ensure_ascii=False))


if __name__ == '__main__':
    main()
