# Product Catalog Deduplication

A conservative Python reference for identifying likely duplicate product records. The script creates a proposed cleaned catalog and an audit file; review candidates before using the cleaned output downstream.

## Matching rule

Records match when normalized product name, buy unit, package, brand, parent category, and category are equal, and the product IDs differ. Normalization trims surrounding whitespace, collapses repeated spaces, and ignores letter case. A row is excluded from matching when product name, buy unit, package, or category is blank. The script does not use fuzzy matching.

## Input and assumptions

Input is a UTF-8 CSV containing `product_id`, `product_name`, `buy_unit`, `package`, `brand`, `parent_category_id`, `category_id`, and `orders`. Product IDs must be populated and unique. `orders` must be non-negative numeric data or blank; blanks count as zero.

The proposed representative is the record with the highest order count. Ties resolve to the lexically first product ID. The cleaned output sums `orders` across matched IDs, which assumes those counts represent distinct activity. Change that rule if the source metric already counts deduplicated products.

## Run

Requires Python and pandas.

```powershell
python deduplicate_catalog.py path\to\catalog.csv --output-dir output
```

The output directory contains:

- `cleaned_catalog.csv`: records with one proposed representative per matched group.
- `duplicate_candidates.csv`: original candidate rows, a group number to connect matching rows, and the recommended representative ID.

Review each group for false positives before merging records. Identical attributes do not prove that two products are interchangeable. This repository contains no source catalog or interview materials.

The script stops if either output file already exists, so it does not silently replace earlier results. Choose a new output directory or move the previous files before rerunning.

## Entrega original (resumo sanitizado)

A entrega da época incluiu análise e código Python para identificar duplicidades em um catálogo. Este repositório demonstra uma regra conservadora de correspondência e revisão de candidatos com entrada sintética; não contém catálogo nem resultados originais.

## Exemplo sintético

O arquivo `examples/catalog_input.csv` contém seis registros inventados. O script gerou os arquivos em `examples/generated/`:

| Grupo | ID recomendado | Pedidos agregados no exemplo |
|---|---:|---:|
| Iogurte | 1001 | 210 |
| Leite | 2002 | 43 |

Os dois grupos resultam em quatro registros no catálogo proposto. A linha sem nome permanece separada e fora da correspondência. Esses valores demonstram o comportamento do script e não são resultados do case original.
