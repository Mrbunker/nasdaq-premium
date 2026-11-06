"""Compare month-end common-date NAV/price observations, not averages of daily returns."""
import datetime as dt
import json
from project import ROOT


def main():
    path = ROOT / 'data/history.json'
    bundle = json.loads(path.read_text())
    for fund in bundle['funds']:
        grouped = {}
        for row in fund['series']:
            if row['close'] is not None:
                grouped.setdefault(row['date'][:7], []).append(row)
        previous = None
        monthly = []
        events = [event['date'] for event in fund['nav_events']]
        for month, rows in sorted(grouped.items()):
            common = [r for r in rows if r['nav'] is not None and r['premium_pct'] is not None]
            end = common[-1] if common else rows[-1]
            partial = month == bundle['cutoff'][:7]
            current = {
                'month': month, 'date': end['date'], 'nav': end['nav'], 'close': end['close'],
                'premium_pct': end['premium_pct'], 'latest_price_date': rows[-1]['date'],
                'prev_month': previous['month'] if previous else None,
                'prev_date': previous['date'] if previous else None,
                'monthly_nav_pct': None, 'monthly_close_pct': None,
                'premium_contribution_pp': None, 'prev_premium_pct': None,
                'premium_change_pp': None, 'is_partial': partial, 'monthly_status': '正常',
            }
            y, m = map(int, month.split('-'))
            expected_previous = (dt.date(y, m, 1) - dt.timedelta(days=1)).strftime('%Y-%m')
            if not common:
                current['monthly_status'] = '当月无净值与价格共同日期，月涨跌留空'
            elif previous is None or previous['month'] != expected_previous:
                current['monthly_status'] = '缺少紧邻前月基准，月涨跌留空'
            elif previous['nav'] is None or previous['premium_pct'] is None:
                current['monthly_status'] = '前月净值基准缺失，月涨跌留空'
            elif any(previous['date'] <= event <= end['date'] for event in events):
                current['monthly_status'] = '跨越份额折算，月涨跌留空'
            else:
                current['monthly_nav_pct'] = (end['nav'] / previous['nav'] - 1) * 100
                current['monthly_close_pct'] = (end['close'] / previous['close'] - 1) * 100
                current['premium_contribution_pp'] = current['monthly_close_pct'] - current['monthly_nav_pct']
                current['prev_premium_pct'] = previous['premium_pct']
                current['premium_change_pp'] = end['premium_pct'] - previous['premium_pct']
            monthly.append(current)
            previous = current
        fund['monthly_series'] = monthly
    bundle['methodology']['monthly_changes'] = {
        'endpoint': '每个自然月采用该月最后一个公布单位净值与场内收盘价同日期均可用的交易日；显示实际统计日，不将旧净值填到新价格日期。',
        'return': '(当月末共同日期值 / 紧邻前月末共同日期值 - 1) × 100；不是日涨跌平均或日涨跌简单相加。',
        'premium_contribution_pp': '场内月涨跌幅 - 净值月涨跌幅，单位百分点。',
        'partial': '当前自然月标记为未结束、月内截至实际共同估值日期。',
        'missing': '缺少当月/前月共同日期或跨越份额折算时不补算、不跨月拼接。',
    }
    path.write_text(json.dumps(bundle, ensure_ascii=False, separators=(",", ":")))
    print('Monthly records:', sum(len(f['monthly_series']) for f in bundle['funds']))


if __name__ == '__main__':
    main()
