# Product Catalog Deduplication

A small data-quality script that flags catalog records with different product IDs but matching normalized attributes. It keeps the highest-order record as the representative and sums order counts within each matched group.

## Input

Provide a UTF-8 CSV with these columns: `product_id`, `product_name`, `buy_unit`, `package`, `brand`, `parent_category_id`, `category_id`, and `orders`. The script reads the source path from the command line and writes two CSVs to a chosen output directory.

## Run

```powershell
python deduplicate_catalog.py path	o\catalog.csv --output-dir output
```

The matching key is a heuristic. It normalizes case and whitespace but does not use fuzzy matching, so spelling variations may remain and genuinely distinct products with identical attributes may be grouped. Review the candidate file before merging records. No source catalog or interview materials are included.
