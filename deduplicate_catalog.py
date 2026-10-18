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
MATCH_REQUIRED_COLUMNS = ['product_name', 'buy_unit', 'package', 'category_id']
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
    data['product_id'] = data['product_id'].str.strip()
    if data['product_id'].isna().any() or data['product_id'].eq('').any():
        parser.error('product_id must be populated on every row.')
    if data['product_id'].duplicated().any():
        parser.error('product_id must be unique; resolve repeated IDs before deduplication.')

    numeric_orders = pd.to_numeric(data['orders'], errors='coerce')
    invalid_orders = data['orders'].notna() & numeric_orders.isna()
    if invalid_orders.any() or numeric_orders.lt(0).any():
        parser.error('orders must contain non-negative numeric values or be blank.')
    data['_orders_numeric'] = numeric_orders.fillna(0)
    keys = normalize_key(data)
    valid_key = keys[MATCH_REQUIRED_COLUMNS].ne('').all(axis=1)
    duplicate_group = valid_key & (
        keys.join(data['product_id'])
        .groupby(KEY_COLUMNS, dropna=False)['product_id']
        .transform('nunique')
        .gt(1)
    )

    candidates = data.loc[duplicate_group].copy()
    candidates = candidates.join(keys.loc[duplicate_group].add_prefix('_key_'))
    key_names = [f'_key_{column}' for column in KEY_COLUMNS]

    if candidates.empty:
        cleaned = data.drop(columns=['_orders_numeric'])
        candidate_output = pd.DataFrame(
            columns=[*data.columns.drop('_orders_numeric'), 'duplicate_group_id', 'recommended_product_id']
        )
    else:
        candidates = candidates.sort_values(
            by=key_names + ['_orders_numeric', 'product_id'],
            ascending=[True] * len(key_names) + [False, True],
            kind='mergesort',
        )
        group = candidates.groupby(key_names, dropna=False, sort=True)
        candidates['duplicate_group_id'] = group.ngroup() + 1
        candidates['recommended_product_id'] = group['product_id'].transform('first')
        group = candidates.groupby(key_names, dropna=False, sort=True)
        representatives = candidates.drop_duplicates(key_names, keep='first').copy()
        totals = group['_orders_numeric'].sum().rename('orders_total').reset_index()
        representatives = representatives.merge(totals, on=key_names, validate='one_to_one')
        representatives['orders'] = representatives['orders_total']
        untouched = data.loc[~duplicate_group].drop(columns=['_orders_numeric'])
        representatives = representatives[data.columns.drop('_orders_numeric')]
        cleaned = pd.concat([untouched, representatives], ignore_index=True)
        candidate_output = candidates[
            [*data.columns.drop('_orders_numeric'), 'duplicate_group_id', 'recommended_product_id']
        ]

    args.output_dir.mkdir(parents=True, exist_ok=True)
    output_paths = [
        args.output_dir / 'cleaned_catalog.csv',
        args.output_dir / 'duplicate_candidates.csv',
    ]
    input_path = args.input_csv.resolve()
    if input_path in [path.resolve() for path in output_paths]:
        parser.error('The input file cannot use an output filename.')
    existing_outputs = [path.name for path in output_paths if path.exists()]
    if existing_outputs:
        parser.error(f'Output file(s) already exist: {", ".join(existing_outputs)}')

    cleaned.to_csv(output_paths[0], index=False, encoding='utf-8-sig')
    candidate_output.to_csv(output_paths[1], index=False, encoding='utf-8-sig')


if __name__ == '__main__':
    main()
