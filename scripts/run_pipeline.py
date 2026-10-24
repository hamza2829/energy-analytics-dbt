"""Local dbt command and CSV/HTML export, shared by Dagster and the CLI."""
import csv
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def run_dbt(*args):
    executable = Path(sys.executable).with_name('dbt.exe' if os.name == 'nt' else 'dbt')
    environment = {**os.environ, 'DBT_SEND_ANONYMOUS_USAGE_STATS': 'false'}
    subprocess.run([str(executable), *args, '--profiles-dir', str(ROOT),
                    '--project-dir', str(ROOT), '--no-use-colors'],
                   cwd=ROOT, env=environment, check=True)


def export_outputs():
    output = ROOT / 'artifacts/monthly_partner_commission.csv'
    output.parent.mkdir(exist_ok=True)
    with duckdb.connect(str(ROOT / 'data/energy.duckdb'), read_only=True) as connection:
        cursor = connection.execute('select * from mart_monthly_partner_commission order by month, partner_id')
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        temporary = output.with_suffix('.tmp')
        with temporary.open('w', newline='', encoding='utf-8') as handle:
            writer = csv.writer(handle, lineterminator='\n')
            writer.writerow(columns)
            writer.writerows(rows)
        temporary.replace(output)
        commission = [dict(zip(columns, row, strict=True)) for row in rows]
        prices = connection.execute('select timestamp_utc, price_eur_per_mwh from stg_prices order by timestamp_utc').fetchall()
        report_cursor = connection.execute('select * from mart_monthly_price_report order by month')
        report_columns = [column[0] for column in report_cursor.description]
        reports = [dict(zip(report_columns, row, strict=True)) for row in report_cursor.fetchall()]
    payload = {
        'generated_at': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
        'prices': [[ts.strftime('%Y-%m-%d %H:%M'), float(price)] for ts, price in prices],
        'commission': commission, 'reports': reports,
    }
    template = (ROOT / 'dashboard/template.html').read_text(encoding='utf-8')
    # All payload fields come from committed, non-user-controlled demo inputs.
    html = template.replace('__DATA__', json.dumps(payload, default=str).replace('</', '<\\/'))
    (ROOT / 'dashboard/index.html').write_text(html, encoding='utf-8')
    print(f'Exported {len(rows)} statements to {output}; dashboard/index.html updated')
    return str(output)


if __name__ == '__main__':
    run_dbt('build')
    export_outputs()
