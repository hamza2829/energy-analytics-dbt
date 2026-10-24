"""Optional online refresh of the committed, fixed historical sample."""
import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
URL = ('https://api.energy-charts.info/price?bzn=DE-LU'
       '&start=2024-01-01T00%3A00Z&end=2024-02-29T23%3A00Z')


def save_sample(payload):
    if 'CC BY 4.0' not in payload.get('license_info', ''):
        raise ValueError('Review the source license before redistributing this data')
    timestamps, prices = payload['unix_seconds'], payload['price']
    expected = list(range(1704067200, 1709251200, 3600))
    if timestamps != expected or len(prices) != len(expected) or any(p is None for p in prices):
        raise ValueError('Expected exactly 1,440 complete hourly prices for Jan-Feb 2024 UTC')
    path = ROOT / 'seeds/raw_prices.csv'
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.writer(handle, lineterminator='\n')
        writer.writerow(['timestamp_utc', 'bidding_zone', 'price_eur_per_mwh'])
        for ts, price in zip(timestamps, prices, strict=True):
            writer.writerow([datetime.fromtimestamp(ts, timezone.utc).strftime('%Y-%m-%d %H:%M:%S'),
                             'DE-LU', f'{price:.2f}'])
    metadata = {
        'source': 'Energy-Charts.info API, Fraunhofer ISE',
        'upstream_attribution': 'Bundesnetzagentur | SMARD.de',
        'url': URL, 'license_info': payload['license_info'],
        'license_url': 'https://creativecommons.org/licenses/by/4.0/',
        'retrieved_date': datetime.now(timezone.utc).date().isoformat(),
        'period': '[2024-01-01 00:00, 2024-03-01 00:00) UTC',
        'unit': payload['unit'], 'rows': len(prices),
        'changes': 'Converted Unix seconds to UTC timestamps; selected three CSV columns; prices formatted to two decimals.',
        'csv_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
    }
    (ROOT / 'data/provenance.json').write_text(json.dumps(metadata, indent=2) + '\n', encoding='utf-8')
    print(f'Saved {len(prices)} real hourly prices to {path}')


if __name__ == '__main__':
    with urlopen(URL, timeout=60) as response:
        save_sample(json.load(response))
