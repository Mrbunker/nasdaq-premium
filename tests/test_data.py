import datetime as dt
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from compute_daily import compute
from project import CHINA, latest_complete_day
from validate_snapshot import validate


def fund(rows, events=()):
    return {'nav_events':[{'date':date} for date in events],
            'series':[{'date':date,'nav':nav,'close':price,
                       'premium_pct':(price/nav-1)*100 if nav and price else None}
                      for date,nav,price in rows]}


class DailyBaselineTests(unittest.TestCase):
    def test_missing_previous_nav_is_not_skipped(self):
        result=compute(fund([('2026-01-05',1,1),('2026-01-06',None,1.02),('2026-01-07',1.1,1.04)]))['series']
        self.assertIsNone(result[1]['daily_nav_pct'])
        self.assertIsNone(result[2]['daily_nav_pct'])
        self.assertIsNone(result[2]['premium_contribution_pp'])
        self.assertAlmostEqual(result[2]['daily_close_pct'],(1.04/1.02-1)*100)

    def test_split_and_following_exchange_interval_are_excluded(self):
        result=compute(fund([('2022-07-01',2.39,2.37),('2022-07-04',.6,2.38),
                             ('2022-07-05',.61,.6),('2022-07-06',.62,.61)],['2022-07-04']))['series']
        self.assertIsNone(result[1]['premium_pct'])
        self.assertIsNone(result[1]['daily_close_pct'])
        self.assertIsNone(result[2]['daily_close_pct'])
        self.assertIsNotNone(result[3]['premium_contribution_pp'])

    def test_contribution_is_return_difference_not_premium_point_change(self):
        row=compute(fund([('2026-01-05',1,1.08),('2026-01-06',1.01,1.107)]))['series'][-1]
        self.assertAlmostEqual(row['daily_nav_pct'],1)
        self.assertAlmostEqual(row['daily_close_pct'],2.5)
        self.assertAlmostEqual(row['premium_contribution_pp'],1.5)
        self.assertNotAlmostEqual(row['premium_change_pp'],1.5)

    def test_first_exchange_record_has_no_invented_return(self):
        row=compute(fund([('2026-01-05',1,1.1)]))['series'][0]
        self.assertIsNone(row['daily_close_pct'])


class SnapshotTests(unittest.TestCase):
    def test_all_committed_daily_and_monthly_identities(self):
        counts=validate(json.loads((ROOT/'data/history.json').read_text()))
        self.assertEqual(counts['funds'],16)
        self.assertGreater(counts['daily_comparisons'],20000)
        self.assertGreater(counts['monthly_comparisons'],1000)

    def test_before_close_excludes_today(self):
        self.assertEqual(latest_complete_day(dt.datetime(2026,11,6,14,59,tzinfo=CHINA)),dt.date(2026,11,5))

    def test_weekend_uses_last_weekday(self):
        self.assertEqual(latest_complete_day(dt.datetime(2026,11,7,18,0,tzinfo=CHINA)),dt.date(2026,11,6))


if __name__ == '__main__':
    unittest.main()
