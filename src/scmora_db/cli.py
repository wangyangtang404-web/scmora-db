"""Command-line interface for scmora-db."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Union

from ._version import __version__
from .catalog import (
    DEFAULT_MAX_AUTO_MATCHES,
    DEFAULT_REPO_ID,
    list_dataset_ids,
    list_detail_sources,
    list_detailed_conditions,
    list_usage_tags,
    search_datasets,
)
from .download import download_datasets
from .exceptions import AmbiguousDatasetError, TooManyMatchesError


def main(argv: Optional[List[str]] = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    try:
        return args.func(args)
    except TooManyMatchesError as exc:
        print(str(exc), file=sys.stderr)
        for dataset_uid in exc.dataset_uids:
            print(dataset_uid)
        return 2
    except AmbiguousDatasetError as exc:
        print(str(exc), file=sys.stderr)
        for dataset_uid in exc.matches:
            print(dataset_uid)
        return 2


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="scmora-db",
        description="Search, download, and load SCMORA .h5mu datasets.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--repo-id", default=DEFAULT_REPO_ID, help="Hugging Face dataset repo ID.")
    parser.add_argument("--revision", default=None, help="Hugging Face revision, branch, or commit.")
    parser.add_argument("--token", default=None, help="Hugging Face token for private datasets.")
    parser.add_argument("--cache-dir", default=None, help="Hugging Face cache directory.")
    parser.add_argument("--metadata-path", default=None, help="Use a local metadata CSV.")
    parser.add_argument(
        "--prefer-remote",
        action="store_true",
        help="Download metadata.csv from Hugging Face instead of using bundled metadata.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    search_parser = subparsers.add_parser("search", help="Search metadata without downloading .h5mu files.")
    _add_filter_args(search_parser)
    search_parser.add_argument("--columns", default=None, help="Comma-separated columns to print.")
    search_parser.add_argument("--limit", type=int, default=None, help="Maximum rows to print.")
    search_parser.set_defaults(func=_cmd_search)

    download_parser = subparsers.add_parser("download", help="Download matching .h5mu files.")
    _add_filter_args(download_parser)
    download_parser.add_argument("--local-dir", default=None, help="Optional local output directory.")
    download_parser.add_argument("--force-download", action="store_true", help="Force redownload.")
    download_parser.add_argument("--max-auto-matches", type=int, default=DEFAULT_MAX_AUTO_MATCHES)
    download_parser.set_defaults(func=_cmd_download)

    load_parser = subparsers.add_parser("load", help="Download and open matching .h5mu files.")
    _add_filter_args(load_parser)
    load_parser.add_argument("--local-dir", default=None, help="Optional local output directory.")
    load_parser.add_argument("--force-download", action="store_true", help="Force redownload.")
    load_parser.add_argument("--max-auto-matches", type=int, default=DEFAULT_MAX_AUTO_MATCHES)
    load_parser.add_argument("--backed", default=None, help='MuData backed mode, for example "r".')
    load_parser.set_defaults(func=_cmd_load)

    list_parser = subparsers.add_parser("list", help="List available metadata values.")
    list_parser.add_argument(
        "field",
        choices=["dataset-ids", "usage-tags", "detailed-conditions", "detail-sources"],
    )
    list_parser.set_defaults(func=_cmd_list)

    return parser


def _add_filter_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dataset-id", action="append", help="Filter by dataset_id. Can be repeated.")
    parser.add_argument("--dataset-uid", action="append", help="Filter by unique gse_id/dataset_id.")
    parser.add_argument("--gse-id", action="append", help="Filter by GSE ID. Can be repeated.")
    parser.add_argument("--detailed-condition", action="append", help="Filter by detailed_condition.")
    parser.add_argument("--usage-tag", action="append", help="Filter by one usage tag.")
    parser.add_argument("--detail-source", action="append", help="Filter by detail_source.")
    parser.add_argument("--condition", action="append", help="Filter by broad condition.")
    parser.add_argument("--sample-type", action="append", help="Filter by sample_type.")
    parser.add_argument("--species", action="append", help="Filter by species.")
    parser.add_argument("--reference", action="append", help="Filter by reference genome.")


def _catalog_kwargs(args) -> dict:
    return {
        "repo_id": args.repo_id,
        "revision": args.revision,
        "token": args.token,
        "cache_dir": args.cache_dir,
        "metadata_path": args.metadata_path,
        "prefer_remote": args.prefer_remote,
    }


def _filter_kwargs(args) -> dict:
    return {
        "dataset_id": args.dataset_id,
        "dataset_uid": args.dataset_uid,
        "gse_id": args.gse_id,
        "detailed_condition": args.detailed_condition,
        "usage_tag": args.usage_tag,
        "detail_source": args.detail_source,
        "condition": args.condition,
        "sample_type": args.sample_type,
        "species": args.species,
        "reference": args.reference,
    }


def _cmd_search(args) -> int:
    df = search_datasets(**_filter_kwargs(args), **_catalog_kwargs(args))
    columns = [
        "dataset_uid",
        "dataset_id",
        "gse_id",
        "detailed_condition",
        "usage_tags",
        "detail_source",
        "file_path",
    ]
    if args.columns:
        columns = [column.strip() for column in args.columns.split(",") if column.strip()]
    if args.limit is not None:
        df = df.head(args.limit)
    print(df.loc[:, columns].to_csv(index=False).rstrip())
    return 0


def _cmd_download(args) -> int:
    paths = download_datasets(
        **_filter_kwargs(args),
        **_catalog_kwargs(args),
        max_auto_matches=args.max_auto_matches,
        local_dir=args.local_dir,
        force_download=args.force_download,
    )
    _print_paths(paths)
    return 0


def _cmd_load(args) -> int:
    from .io import load_datasets

    objects = load_datasets(
        **_filter_kwargs(args),
        **_catalog_kwargs(args),
        max_auto_matches=args.max_auto_matches,
        local_dir=args.local_dir,
        force_download=args.force_download,
        backed=args.backed,
    )
    if not isinstance(objects, list):
        objects = [objects]
    for obj in objects:
        print(_summarize_mudata(obj))
    return 0


def _cmd_list(args) -> int:
    kwargs = _catalog_kwargs(args)
    if args.field == "dataset-ids":
        values = list_dataset_ids(**kwargs)
    elif args.field == "usage-tags":
        values = list_usage_tags(**kwargs)
    elif args.field == "detailed-conditions":
        values = list_detailed_conditions(**kwargs)
    else:
        values = list_detail_sources(**kwargs)

    for value in values:
        print(value)
    return 0


def _print_paths(paths: Union[str, List[str]]) -> None:
    if isinstance(paths, str):
        print(paths)
        return
    for path in paths:
        print(path)


def _summarize_mudata(obj) -> str:
    n_obs = getattr(obj, "n_obs", "?")
    n_vars = getattr(obj, "n_vars", "?")
    mod = getattr(obj, "mod", {})
    modalities = ",".join(mod.keys()) if hasattr(mod, "keys") else "?"
    return f"MuData(n_obs={n_obs}, n_vars={n_vars}, modalities={modalities})"


if __name__ == "__main__":
    raise SystemExit(main())
