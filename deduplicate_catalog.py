from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

KEY_COLUMNS = [
    'product_name',
    'buy_unit',
    'package',
    'brand',
    'parent_category_id',
    'category_id',
]
REQUIRED_COLUMNS = ['product_id', *KEY_COLUMNS, 'orders']


def normalize_key(frame: pd.DataFrame) -> pd.DataFrame:
    key = frame[KEY_COLUMNS].copy()
    for column in KEY_COLUMNS:
        key[column] = (
            key[column]
            .astype('string')
            .fillna('')
            .str.lower()
            .str.strip()
            .str.replace(r'\s+', ' ', regex=True)
        )
    return key


def main() -> None:
    parser = argparse.ArgumentParser(description='Find likely duplicate product records.')
    parser.add_argument('input_csv', type=Path)
    parser.add_argument('--output-dir', type=Path, default=Path('output'))
    args = parser.parse_args()

    data = pd.read_csv(args.input_csv, dtype={'product_id': 'string'})
    missing = sorted(set(REQUIRED_COLUMNS) - set(data.columns))
    if missing:
        parser.error(f'Missing required columns: {", ".join(missing)}')

    data = data.copy()
    data['_orders_numeric'] = pd.to_numeric(data['orders'], errors='coerce').fillna(0)
    keys = normalize_key(data)
    duplicate_group = keys.groupby(KEY_COLUMNS, dropna=False)['product_id'].transform('nunique') > 1

    candidates = data.loc[duplicate_group].copy()
    candidates['_orders_numeric'] = pd.to_numeric(candidates['orders'], errors='coerce').fillna(0)
    candidates = candidates.join(keys.loc[duplicate_group].add_prefix('_key_'))
    key_names = [f'_key_{column}' for column in KEY_COLUMNS]

    if candidates.empty:
        cleaned = data.drop(columns=['_orders_numeric'])
    else:
        group = candidates.groupby(key_names, dropna=False, sort=False)
        representative_indices = group['_orders_numeric'].idxmax()
        representatives = candidates.loc[representative_indices].copy()
        totals = group['_orders_numeric'].sum().rename('orders_total').reset_index()
        representatives = representatives.merge(totals, on=key_names, validate='one_to_one')
        representatives['orders'] = representatives['orders_total']
        untouched = data.loc[~duplicate_group].drop(columns=['_orders_numeric'])
        cleaned = pd.concat(
            [untouched, representatives.drop(columns=key_names + ['_orders_numeric', 'orders_total'])],
            ignore_index=True,
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    cleaned.to_csv(args.output_dir / 'cleaned_catalog.csv', index=False, encoding='utf-8-sig')
    candidates.drop(columns=key_names + ['_orders_numeric'], errors='ignore').to_csv(
        args.output_dir / 'duplicate_candidates.csv', index=False, encoding='utf-8-sig'
    )


if __name__ == '__main__':
    main()
