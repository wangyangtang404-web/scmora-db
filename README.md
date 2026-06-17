# scmora-db

`scmora-db` is a small Python package for searching, downloading, and loading
SCMORA `.h5mu` datasets from the Hugging Face dataset repository
`shiny321/genome-db`.

The package ships with a lightweight metadata catalog. Large `.h5mu` files stay
on Hugging Face and are downloaded only when requested.

## Installation

Python 3.10 or newer is required.

```bash
pip install scmora-db
```

This installs everything needed to search, download, and load `.h5mu` files as
MuData objects.


For local development:

```bash
cd path/to/pkg
pip install -e ".[dev]"
```

## Python API

```python
from scmora_db import search_datasets, download_datasets, load_datasets

catalog = search_datasets(dataset_id="GSM5085810_GM12878_rep1")

paths = download_datasets(
    detailed_condition="Control",
    usage_tag="control",
)

mdata = load_datasets(
    dataset_id="GSM5085810_GM12878_rep1",
    backed="r",
)
```

Supported filters:

- `dataset_id`
- `dataset_uid`
- `gse_id`
- `detailed_condition`
- `usage_tag`
- `detail_source`
- `condition`
- `sample_type`
- `species`
- `reference`

`dataset_uid` is the safest unique identifier and is formatted as
`GSE_id/dataset_id`.

## Multi-Match Rule

`download_datasets()` and `load_datasets()` use this default rule:

- one match: return one path or one MuData object
- two to five matches: return a list
- more than five matches: stop and report all matched `dataset_uid` values

This prevents accidental large downloads.

## Command Line

```bash
scmora-db search --usage-tag control
scmora-db search --detailed-condition Control
scmora-db search --detail-source "GM12878 (Cell Line)"
scmora-db download --dataset-id GSM5085810_GM12878_rep1
scmora-db load --dataset-id GSM5085810_GM12878_rep1 --backed r
```

List available metadata values:

```bash
scmora-db list dataset-ids
scmora-db list dataset-uids
scmora-db list gse-ids
scmora-db list usage-tags
scmora-db list groups
scmora-db list condition
scmora-db list detailed-conditions
scmora-db list detail-sources
scmora-db list sample-types
scmora-db list species
scmora-db list references
```

Useful options:

```bash
scmora-db download --cache-dir ./hf-cache --local-dir ./data
scmora-db search --prefer-remote
scmora-db download --revision main
scmora-db download --token hf_xxx
```

## Metadata

The bundled metadata file contains 277 datasets and these core columns:

- `dataset_uid`
- `dataset_id`
- `gse_id`
- `file_path`
- `file_name`
- `species`
- `reference`
- `group`
- `usage_primary`
- `usage_tags`
- `sample_type`
- `detail_source`
- `condition`
- `detailed_condition`

The `file_path` values are relative to `shiny321/genome-db`, for example:

```text
GSE166797/GSM5085810_GM12878_rep1.h5mu
```

## Build and Publish

```bash
python -m pip install -U build twine
python -m build
python -m twine check dist/*
python -m twine upload --repository testpypi dist/*
```

After testing on TestPyPI:

```bash
python -m twine upload dist/*
```
