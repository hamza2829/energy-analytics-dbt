"""Check mart arithmetic against the CSV inputs using Python Decimal, not SQL."""
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

import duckdb
from dagster import build_schedule_context

from orchestration import monthly_schedule
from scripts.run_pipeline import ROOT


def main():
    sales = list(csv.DictReader((ROOT / 'seeds/partner_sales.csv').open(encoding='utf-8')))
    rules = {r['partner_id']: r for r in csv.DictReader((ROOT / 'seeds/commission_rules.csv').open(encoding='utf-8'))}
    prices = list(csv.DictReader((ROOT / 'seeds/raw_prices.csv').open(encoding='utf-8')))
    provenance = json.loads((ROOT / 'data/provenance.json').read_text())
    assert hashlib.sha256((ROOT / 'seeds/raw_prices.csv').read_bytes()).hexdigest() == provenance['csv_sha256']
    assert len(prices) == 1440 and len(sales) == 100 and len(rules) == 5
    kwh = defaultdict(Decimal)
    days, months = defaultdict(list), defaultdict(list)
    for row in sales:
        kwh[(row['month'], row['partner_id'])] += Decimal(row['kwh'])
    for row in prices:
        days[row['timestamp_utc'][:10]].append(row)
        months[row['timestamp_utc'][:7]].append(Decimal(row['price_eur_per_mwh']))
    with duckdb.connect(str(ROOT / 'data/energy.duckdb'), read_only=True) as connection:
        statements = connection.execute('select month, partner_id, total_kwh, commission_eur from mart_monthly_partner_commission order by month, partner_id').fetchall()
        assert len(statements) == 10
        for month, partner, total, commission in statements:
            expected_kwh = kwh[(month.isoformat(), partner)]
            rule = rules[partner]
            expected = (expected_kwh * Decimal(rule['retail_rate_eur_per_kwh']) * Decimal(rule['commission_pct'])).quantize(Decimal('.01'), rounding=ROUND_HALF_UP)
            assert total == expected_kwh and commission == expected, (month, partner, commission, expected)
        daily = connection.execute('select price_date_utc, min_price_eur_per_mwh, max_price_eur_per_mwh, avg_price_eur_per_mwh, cheapest_3_hours_utc from int_daily_price_stats').fetchall()
        assert len(daily) == 60
        for day, minimum, maximum, average, cheapest in daily:
            rows = days[day.isoformat()]
            values = [Decimal(r['price_eur_per_mwh']) for r in rows]
            ranked = sorted(rows, key=lambda r: (Decimal(r['price_eur_per_mwh']), r['timestamp_utc']))
            assert minimum == min(values) and maximum == max(values)
            assert abs(Decimal(str(average)) - sum(values) / len(values)) < Decimal('.000001')
            assert cheapest == [int(r['timestamp_utc'][11:13]) for r in ranked[:3]]
        reports = connection.execute('select month, hour_count, avg_price_eur_per_mwh from mart_monthly_price_report order by month').fetchall()
        for month, count, average in reports:
            values = months[month.strftime('%Y-%m')]
            assert count == len(values)
            assert abs(Decimal(str(average)) - sum(values) / len(values)) <= Decimal('.000001')
    assert monthly_schedule.cron_schedule == '0 6 1 * *'
    assert monthly_schedule.execution_timezone == 'Europe/Berlin'
    context = build_schedule_context(scheduled_execution_time=datetime(2026, 11, 1, 5, tzinfo=timezone.utc))
    assert len(monthly_schedule.evaluate_tick(context).run_requests) == 1
    result = json.loads((ROOT / 'target/run_results.json').read_text())
    # Docs generation can serialize successful test statuses as "success".
    # Identify tests by their resource ID so the count also works after docs.
    tests = [r for r in result['results'] if r['unique_id'].startswith('test.')]
    passed = sum(r['status'] in ('pass', 'success') for r in tests)
    assert len(tests) == 44 and passed == 44
    assert all(r['status'] in ('pass', 'success') for r in result['results'])
    summary = {'models_verified': 5, 'data_tests_passed': passed, 'price_hours': 1440,
               'daily_rows_checked': len(daily), 'commission_rows_checked': len(statements),
               'monthly_price_rows_checked': len(reports), 'schedule_evaluation_run_requests': 1,
               'example': {'month': str(statements[0][0]), 'partner_id': statements[0][1],
                           'kwh': str(statements[0][2]), 'commission_eur': str(statements[0][3])}}
    (ROOT / 'verification').mkdir(exist_ok=True)
    (ROOT / 'verification/results.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
