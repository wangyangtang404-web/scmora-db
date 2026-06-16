"""Download .h5mu files from Hugging Face."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from .catalog import DEFAULT_MAX_AUTO_MATCHES, DEFAULT_REPO_ID, DEFAULT_REPO_TYPE, resolve_matches


def download_datasets(
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
) -> Union[str, List[str]]:
    """Download matching ``.h5mu`` files and return local paths.

    If one dataset matches, a single path string is returned. If two to five
    datasets match, a list of path strings is returned. More than five matches
    raises ``TooManyMatchesError``.
    """

    result = resolve_matches(
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
        require_unique_dataset_id=True,
    )

    if result.rows.empty:
        return []

    try:
        from huggingface_hub import hf_hub_download
    except ImportError as exc:
        raise ImportError(
            "Downloading datasets requires the dependency 'huggingface_hub'. "
            "Install scmora-db with its default dependencies: pip install scmora-db"
        ) from exc

    paths = []
    for _, row in result.rows.iterrows():
        path = hf_hub_download(
            repo_id=repo_id,
            repo_type=DEFAULT_REPO_TYPE,
            filename=row["file_path"],
            revision=revision,
            token=token,
            cache_dir=cache_dir,
            local_dir=local_dir,
            force_download=force_download,
        )
        paths.append(path)

    return paths[0] if len(paths) == 1 else paths
