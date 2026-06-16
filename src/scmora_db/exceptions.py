"""Custom exceptions for scmora-db."""


class ScmoraDbError(Exception):
    """Base class for scmora-db errors."""


class AmbiguousDatasetError(ScmoraDbError):
    """Raised when a dataset_id query matches multiple datasets."""

    def __init__(self, dataset_id, matches):
        self.dataset_id = dataset_id
        self.matches = list(matches)
        message = (
            f"dataset_id {dataset_id!r} matched multiple datasets. "
            "Use dataset_uid or add gse_id to choose one: "
            + ", ".join(self.matches)
        )
        super().__init__(message)


class TooManyMatchesError(ScmoraDbError):
    """Raised when a download or load query matches too many datasets."""

    def __init__(self, count, dataset_uids, limit):
        self.count = count
        self.dataset_uids = list(dataset_uids)
        self.limit = limit
        ids = ", ".join(self.dataset_uids)
        message = (
            f"Query matched {count} datasets, which is more than the automatic "
            f"limit of {limit}. Matched dataset_uids: {ids}"
        )
        super().__init__(message)
