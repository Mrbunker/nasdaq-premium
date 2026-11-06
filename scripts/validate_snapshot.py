"""Validate the committed data and the baseline rules used by both chart modes."""
import json
import math
from project import DATA, ROOT


def validate(bundle):
    expected = {f['code'] for f in json.loads((ROOT/'config/funds.json').read_text())}
    assert not bundle.get('errors'), 'Data acquisition errors exist'
    assert {f['code'] for f in bundle['funds']} == expected, 'Unexpected fund coverage'
    daily_count = monthly_count = 0
    for fund in bundle['funds']:
        dates = [row['date'] for row in fund['series']]
        assert dates == sorted(set(dates)), fund['code']+' dates are not unique and sorted'
        previous = None
        for row in fund['series']:
            assert row['date'] <= bundle['cutoff']
            for key in ['nav','close']:
                if row[key] is not None:
                    assert math.isfinite(row[key]) and row[key] > 0
            if row['premium_pct'] is not None:
                assert row['nav'] and row['close']
                assert abs(row['premium_pct']-(row['close']/row['nav']-1)*100) < 1e-8
            if row['premium_contribution_pp'] is not None:
                assert previous is not None and previous['nav'] is not None and row['nav'] is not None
                assert row['prev_trade_date'] == previous['date']
                assert abs(row['daily_nav_pct']-(row['nav']/previous['nav']-1)*100) < 1e-8
                assert abs(row['daily_close_pct']-(row['close']/previous['close']-1)*100) < 1e-8
                assert abs(row['premium_contribution_pp']-row['daily_close_pct']+row['daily_nav_pct']) < 1e-8
                daily_count += 1
            if row['close'] is not None:
                previous = row
        previous = None
        for row in fund['monthly_series']:
            if row['monthly_nav_pct'] is not None:
                assert previous is not None
                assert abs(row['monthly_nav_pct']-(row['nav']/previous['nav']-1)*100) < 1e-8
                assert abs(row['monthly_close_pct']-(row['close']/previous['close']-1)*100) < 1e-8
                assert abs(row['premium_contribution_pp']-row['monthly_close_pct']+row['monthly_nav_pct']) < 1e-8
                monthly_count += 1
            assert row['date'][:7] == row['month']
            if row['is_partial']:
                assert row['month'] == bundle['cutoff'][:7]
            previous = row
    return {'funds':len(expected),'daily_comparisons':daily_count,'monthly_comparisons':monthly_count}


if __name__ == '__main__':
    print(json.dumps(validate(json.loads((DATA/'history.json').read_text())),ensure_ascii=False))
