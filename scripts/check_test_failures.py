"""Prove the two custom dbt tests fail on bad data, then restore with dbt build.

Only the generated DuckDB tables are changed. Committed CSV seeds are untouched.
Run while no other process is writing the database.
"""
import json
import subprocess
import duckdb

from scripts.run_pipeline import ROOT, export_outputs, run_dbt


def main():
    evidence = []
    cases = [
        ('missing_hour', 'no_missing_price_hours',
         "delete from stg_prices where timestamp_utc = timestamp '2024-01-15 12:00:00'", 1),
        ('missing_whole_day', 'no_missing_price_hours',
         "delete from stg_prices where price_date_utc = date '2024-01-15'", 24),
        ('duplicate_hour', 'no_missing_price_hours',
         "insert into stg_prices select * from stg_prices where timestamp_utc = timestamp '2024-01-15 12:00:00'", 1),
        ('off_grid_hour', 'no_missing_price_hours',
         "update stg_prices set timestamp_utc = timestamp_utc + interval '30 minutes' where timestamp_utc = timestamp '2024-01-15 12:00:00'", 2),
        ('negative_commission', 'commission_never_negative',
         "update mart_monthly_partner_commission set commission_eur = -1 where statement_id = '2024-01_P01'", 1),
    ]
    run_dbt('build')
    try:
        with duckdb.connect(str(ROOT / 'data/energy.duckdb')) as connection:
            connection.execute('create or replace table backup_prices as select * from stg_prices')
            connection.execute('create or replace table backup_commission as select * from mart_monthly_partner_commission')
        for name, test, mutation, expected_failures in cases:
            with duckdb.connect(str(ROOT / 'data/energy.duckdb')) as connection:
                connection.execute('delete from stg_prices')
                connection.execute('insert into stg_prices select * from backup_prices')
                connection.execute('delete from mart_monthly_partner_commission')
                connection.execute('insert into mart_monthly_partner_commission select * from backup_commission')
                connection.execute(mutation)
            returncode = 0
            try:
                run_dbt('test', '--select', test)
            except subprocess.CalledProcessError as error:
                returncode = error.returncode
            results = json.loads((ROOT / 'target/run_results.json').read_text())['results']
            result = next(r for r in results if r['unique_id'].endswith('.' + test))
            if returncode != 1 or result['status'] != 'fail' or result['failures'] != expected_failures:
                raise AssertionError(f'{name}: expected a data test failure, got {returncode}, {result}')
            evidence.append({'case': name, 'dbt_test': test, 'status': result['status'],
                             'failing_rows': result['failures'], 'exit_code': returncode})
    finally:
        with duckdb.connect(str(ROOT / 'data/energy.duckdb')) as connection:
            connection.execute('drop table if exists backup_prices')
            connection.execute('drop table if exists backup_commission')
        run_dbt('build')
        export_outputs()
    final_results = json.loads((ROOT / 'target/run_results.json').read_text())['results']
    summary = {'intentional_failure_checks': evidence,
               'restored_build_all_successful': all(r['status'] in ('success', 'pass') for r in final_results),
               'restored_data_tests_passed': sum(r['status'] == 'pass' for r in final_results)}
    path = ROOT / 'verification/failure_checks.json'
    path.parent.mkdir(exist_ok=True)
    path.write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
