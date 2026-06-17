"""Search, download, and load SCMORA .h5mu datasets."""

from ._version import __version__
from .catalog import (
    DEFAULT_REPO_ID,
    MatchResult,
    list_dataset_ids,
    list_detail_sources,
    list_detailed_conditions,
    list_usage_tags,
    list_values,
    load_catalog,
    resolve_matches,
    search_datasets,
)
from .exceptions import AmbiguousDatasetError, ScmoraDbError, TooManyMatchesError

__all__ = [
    "AmbiguousDatasetError",
    "DEFAULT_REPO_ID",
    "MatchResult",
    "ScmoraDbError",
    "TooManyMatchesError",
    "__version__",
    "download_datasets",
    "list_dataset_ids",
    "list_detail_sources",
    "list_detailed_conditions",
    "list_usage_tags",
    "list_values",
    "load_catalog",
    "load_datasets",
    "resolve_matches",
    "search_datasets",
]


def download_datasets(*args, **kwargs):
    """Download matching .h5mu files from Hugging Face."""

    from .download import download_datasets as _download_datasets

    return _download_datasets(*args, **kwargs)


def load_datasets(*args, **kwargs):
    """Download and load matching .h5mu files with mudata.read_h5mu."""

    from .io import load_datasets as _load_datasets

    return _load_datasets(*args, **kwargs)
