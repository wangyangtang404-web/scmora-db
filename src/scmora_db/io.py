"""Load .h5mu datasets as MuData objects."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from .catalog import DEFAULT_MAX_AUTO_MATCHES, DEFAULT_REPO_ID
from .download import download_datasets


def load_datasets(
    *,
    dataset_id: Optional[Union[str, List[str]]] = None,
    dataset_uid: Optional[Union[str, List[str]]] = None,
    gse_id: Optional[Union[str, List[str]]] = None,
    detailed_condition: Optional[Union[str, List[str]]] = None,
    usage_tag: Optional[Union[str, List[str]]] = None,
    detail_source: Optional[Union[str, List[str]]] = None,
    condition: Optional[Union[str, List[str]]] = None,
    sample_type: Optional[Union[str, List[str]]] = None,
    species: Optional[Union[str, List[str]]] = None,
    reference: Optional[Union[str, List[str]]] = None,
    repo_id: str = DEFAULT_REPO_ID,
    revision: Optional[str] = None,
    token: Optional[Union[str, bool]] = None,
    cache_dir: Optional[Union[str, Path]] = None,
    metadata_path: Optional[Union[str, Path]] = None,
    prefer_remote: bool = False,
    max_auto_matches: int = DEFAULT_MAX_AUTO_MATCHES,
    local_dir: Optional[Union[str, Path]] = None,
    force_download: bool = False,
    backed: Optional[str] = None,
) -> Union[object, List[object]]:
    """Download and read matching datasets with ``mudata.read_h5mu``."""

    try:
        import mudata as md
    except ImportError as exc:
        raise ImportError(
            "Loading .h5mu files requires the optional dependency 'mudata'. "
            "Install it with: pip install 'scmora-db[load]'"
        ) from exc

    paths = download_datasets(
        dataset_id=dataset_id,
        dataset_uid=dataset_uid,
        gse_id=gse_id,
        detailed_condition=detailed_condition,
        usage_tag=usage_tag,
        detail_source=detail_source,
        condition=condition,
        sample_type=sample_type,
        species=species,
        reference=reference,
        repo_id=repo_id,
        revision=revision,
        token=token,
        cache_dir=cache_dir,
        metadata_path=metadata_path,
        prefer_remote=prefer_remote,
        max_auto_matches=max_auto_matches,
        local_dir=local_dir,
        force_download=force_download,
    )

    if isinstance(paths, str):
        return md.read_h5mu(paths, backed=backed)

    objects = [md.read_h5mu(path, backed=backed) for path in paths]
    return objects
