import json
import tempfile
import unittest
from pathlib import Path

from history_audit import audit


class HistoricalEvidenceTests(unittest.TestCase):
    def test_missing_conflicting_and_out_of_window_evidence_cannot_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {'months': ['2026-07', '2026-08', '2026-09'],
                      'targets': [{'name': n, 'profile_id': n} for n in ['positive', 'absent', 'conflict']],
                      'board_files': [], 'article_files': ['articles.json']}
            for month in config['months']:
                rows = [{'accountName': n, 'accountLink': 'https://www.xiaohongshu.com/user/profile/' + n,
                         'rankPeriod': '月榜', 'rankDate': month + '-01', 'fansGrowth': '1.23w'}
                        for n in ['positive', 'conflict']]
                if month == '2026-08':
                    rows.append({**rows[1], 'fansGrowth': '-2'})
                filename = month + '.json'
                config['board_files'].append(filename)
                (root / filename).write_text(json.dumps({'payload': {'rankDate': month + '-01'},
                                                        'response': {'code': 2000, 'data': rows}}))
            (root / 'articles.json').write_text(json.dumps({
                'payload': {'keyword': 'test', 'startDate': '2026-07-21', 'endDate': '2026-08-19'},
                'response': {'code': 2000, 'data': {'articles': [
                    {'id': 'in', 'createTime': '2026-08-01'},
                    {'id': 'out', 'createTime': '2026-10-01'},
                    {'id': 'unknown', 'createTime': None}],
                    'latestHotArticles': [{'id': 'fallback', 'createTime': '2026-08-01'}]}}}))
            result = audit(config, root)
            positive, absent, conflict = result['targets']
            self.assertEqual(positive['growth_verdict'], 'three_positive_months')
            self.assertEqual(positive['months'][0]['fans_growth'], 12300)
            self.assertTrue(positive['months'][0]['approximate'])
            self.assertEqual(absent['growth_verdict'], 'insufficient_evidence')
            self.assertIsNone(absent['months'][0]['fans_growth'])
            self.assertEqual(conflict['growth_verdict'], 'insufficient_evidence')
            self.assertEqual(conflict['months'][1]['status'], 'conflict_or_unknown')
            coverage = result['article_coverage'][0]
            self.assertEqual((coverage['accepted'], coverage['excluded'], coverage['fallback_excluded']), (1, 2, 1))
            self.assertEqual(len(result['articles']), 3)

    def test_nonconsecutive_months_are_rejected(self):
        with self.assertRaises(ValueError):
            audit({'months': ['2026-07', '2026-08', '2026-10']}, Path('.'))


if __name__ == '__main__':
    unittest.main()
