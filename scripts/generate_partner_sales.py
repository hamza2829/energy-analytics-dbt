"""Generate 5 partners x 10 customers x 2 months, using seed 42."""
import csv
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def generate():
    rng = random.Random(42)
    rows = []
    for month in ['2024-01-01', '2024-02-01']:
        for partner in range(1, 6):
            for customer in range(1, 11):
                customer_type = 'business' if customer > 8 else 'household'
                kwh = rng.randint(70000, 180000) if customer_type == 'business' else rng.randint(12000, 50000)
                rows.append([month, f'P{partner:02}', f'P{partner:02}-C{customer:02}',
                             customer_type, f'{kwh / 100:.2f}'])
    path = ROOT / 'seeds/partner_sales.csv'
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['month', 'partner_id', 'customer_id', 'customer_type', 'kwh'])
        writer.writerows(rows)
    print(f'Saved {len(rows)} synthetic monthly customer rows (seed 42)')


if __name__ == '__main__':
    generate()
