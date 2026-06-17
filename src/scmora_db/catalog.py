"""Metadata catalog access and filtering."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Union

import pandas as pd

from .exceptions import AmbiguousDatasetError, TooManyMatchesError

DEFAULT_REPO_ID = "shiny321/genome-db"
DEFAULT_REPO_TYPE = "dataset"
DEFAULT_METADATA_FILENAME = "metadata.csv"
DEFAULT_MAX_AUTO_MATCHES = 5
LISTABLE_FIELDS = {
    "condition": "condition",
    "dataset-id": "dataset_id",
    "dataset-ids": "dataset_id",
    "dataset-uid": "dataset_uid",
    "dataset-uids": "dataset_uid",
    "detailed-condition": "detailed_condition",
    "detailed-conditions": "detailed_condition",
    "detail-source": "detail_source",
    "detail-sources": "detail_source",
    "group": "group",
    "groups": "group",
    "gse-id": "gse_id",
    "gse-ids": "gse_id",
    "reference": "reference",
    "references": "reference",
    "sample-type": "sample_type",
    "sample-types": "sample_type",
    "species": "species",
    "usage-primary": "usage_primary",
    "usage-primaries": "usage_primary",
    "usage-tag": "usage_tags",
    "usage-tags": "usage_tags",
}


@dataclass(frozen=True)
class MatchResult:
    """A resolved query and the matching rows."""

    rows: pd.DataFrame
    matched_ids: List[str]

    @property
    def count(self) -> int:
        return len(self.rows)

    @property
    def is_single(self) -> bool:
        return self.count == 1


def load_catalog(
    repo_id: str = DEFAULT_REPO_ID,
    *,
    revision: Optional[str] = None,
    token: Optional[Union[str, bool]] = None,
    cache_dir: Optional[Union[str, Path]] = None,
    metadata_path: Optional[Union[str, Path]] = None,
    prefer_remote: bool = False,
) -> pd.DataFrame:
    """Load the dataset metadata catalog.

    By default this reads the metadata bundled with the package. Set
    ``prefer_remote=True`` to download ``metadata.csv`` from Hugging Face first.
    """

    if metadata_path is not None:
        path = Path(metadata_path)
    elif prefer_remote:
        from huggingface_hub import hf_hub_download

        path = Path(
            hf_hub_download(
                repo_id=repo_id,
                repo_type=DEFAULT_REPO_TYPE,
                filename=DEFAULT_METADATA_FILENAME,
                revision=revision,
                token=token,
                cache_dir=cache_dir,
            )
        )
    else:
        path = Path(__file__).with_name(DEFAULT_METADATA_FILENAME)

    return _normalize_catalog(_read_metadata_csv(path))


def search_datasets(
    *,
    dataset_id: Optional[Union[str, Iterable[str]]] = None,
    dataset_uid: Optional[Union[str, Iterable[str]]] = None,
    gse_id: Optional[Union[str, Iterable[str]]] = None,
    detailed_condition: Optional[Union[str, Iterable[str]]] = None,
    usage_tag: Optional[Union[str, Iterable[str]]] = None,
    detail_source: Optional[Union[str, Iterable[str]]] = None,
    condition: Optional[Union[str, Iterable[str]]] = None,
    sample_type: Optional[Union[str, Iterable[str]]] = None,
    species: Optional[Union[str, Iterable[str]]] = None,
    reference: Optional[Union[str, Iterable[str]]] = None,
    repo_id: str = DEFAULT_REPO_ID,
    revision: Optional[str] = None,
    token: Optional[Union[str, bool]] = None,
    cache_dir: Optional[Union[str, Path]] = None,
    metadata_path: Optional[Union[str, Path]] = None,
    prefer_remote: bool = False,
    case_sensitive: bool = False,
) -> pd.DataFrame:
    """Search datasets by metadata fields.

    ``usage_tag`` matches individual semicolon-separated tags in ``usage_tags``.
    Other text filters use exact matching by default, case-insensitively.
    """

    df = load_catalog(
        repo_id=repo_id,
        revision=revision,
        token=token,
        cache_dir=cache_dir,
        metadata_path=metadata_path,
        prefer_remote=prefer_remote,
    )

    filters = {
        "dataset_uid": dataset_uid,
        "dataset_id": dataset_id,
        "gse_id": gse_id,
        "detailed_condition": detailed_condition,
        "detail_source": detail_source,
        "condition": condition,
        "sample_type": sample_type,
        "species": species,
        "reference": reference,
    }
    for column, values in filters.items():
        if values is not None:
            df = df[_isin(df[column], values, case_sensitive=case_sensitive)]

    if usage_tag is not None:
        df = df[_has_usage_tag(df["usage_tags"], usage_tag, case_sensitive=case_sensitive)]

    return df.reset_index(drop=True)


def resolve_matches(
    *,
    max_auto_matches: int = DEFAULT_MAX_AUTO_MATCHES,
    require_unique_dataset_id: bool = False,
    **search_kwargs,
) -> MatchResult:
    """Resolve a query for download/load operations."""

    rows = search_datasets(**search_kwargs)
    matched_ids = rows["dataset_uid"].astype(str).tolist()

    if rows.empty:
        return MatchResult(rows=rows, matched_ids=matched_ids)

    if require_unique_dataset_id and search_kwargs.get("dataset_id") is not None:
        if len(rows) > 1 and search_kwargs.get("dataset_uid") is None and search_kwargs.get("gse_id") is None:
            raise AmbiguousDatasetError(search_kwargs["dataset_id"], matched_ids)

    if len(rows) > max_auto_matches:
        raise TooManyMatchesError(len(rows), matched_ids, max_auto_matches)

    return MatchResult(rows=rows, matched_ids=matched_ids)


def list_dataset_ids(**catalog_kwargs) -> List[str]:
    """Return sorted dataset IDs."""

    return list_values("dataset-id", **catalog_kwargs)


def list_detailed_conditions(**catalog_kwargs) -> List[str]:
    """Return sorted detailed conditions."""

    return list_values("detailed-condition", **catalog_kwargs)


def list_detail_sources(**catalog_kwargs) -> List[str]:
    """Return sorted detail sources."""

    return list_values("detail-source", **catalog_kwargs)


def list_usage_tags(**catalog_kwargs) -> List[str]:
    """Return sorted individual usage tags."""

    return list_values("usage-tag", **catalog_kwargs)


def list_values(field: str, **catalog_kwargs) -> List[str]:
    """Return sorted unique values for a metadata field.

    ``field`` accepts CLI-style names such as ``usage-tags`` and metadata column
    names such as ``usage_tags``.
    """

    normalized = field.strip().replace("_", "-")
    column = LISTABLE_FIELDS.get(normalized, field.strip())
    df = load_catalog(**catalog_kwargs)

    if column not in df.columns:
        choices = ", ".join(sorted(LISTABLE_FIELDS))
        raise ValueError(f"Unknown list field {field!r}. Available fields: {choices}")

    if column != "usage_tags":
        return sorted(value for value in df[column].dropna().astype(str).unique() if value)

    tags = set()
    for value in df["usage_tags"].dropna().astype(str):
        tags.update(tag.strip() for tag in value.split(";") if tag.strip())
    return sorted(tags)


def _normalize_catalog(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(column).strip() for column in df.columns]

    required = {
        "dataset_uid",
        "dataset_id",
        "gse_id",
        "file_path",
        "usage_tags",
        "detail_source",
        "detailed_condition",
    }
    missing = sorted(required - set(df.columns))
    if missing:
        raise ValueError(f"Metadata catalog is missing required columns: {', '.join(missing)}")

    for column in df.columns:
        if pd.api.types.is_object_dtype(df[column]):
            df[column] = df[column].fillna("").astype(str).str.strip()

    return df


def _read_metadata_csv(path: Union[str, Path]) -> pd.DataFrame:
    with Path(path).open("r", encoding="utf-8", newline="") as handle:
        return pd.read_csv(handle)


def _as_list(values: Union[str, Iterable[str]]) -> List[str]:
    if isinstance(values, str):
        return [values]
    return [str(value) for value in values]


def _normalize_value(value: str, *, case_sensitive: bool) -> str:
    value = str(value).strip()
    return value if case_sensitive else value.casefold()


def _isin(series: pd.Series, values: Union[str, Iterable[str]], *, case_sensitive: bool) -> pd.Series:
    normalized_values = {
        _normalize_value(value, case_sensitive=case_sensitive)
        for value in _as_list(values)
    }
    normalized_series = series.astype(str).map(
        lambda value: _normalize_value(value, case_sensitive=case_sensitive)
    )
    return normalized_series.isin(normalized_values)


def _has_usage_tag(series: pd.Series, values: Union[str, Iterable[str]], *, case_sensitive: bool) -> pd.Series:
    wanted = {
        _normalize_value(value, case_sensitive=case_sensitive)
        for value in _as_list(values)
    }

    def has_tag(value: str) -> bool:
        tags = {
            _normalize_value(tag, case_sensitive=case_sensitive)
            for tag in str(value).split(";")
            if tag.strip()
        }
        return bool(tags & wanted)

    return series.astype(str).map(has_tag)
