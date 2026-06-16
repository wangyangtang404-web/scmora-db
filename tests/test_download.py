import pytest

from scmora_db import TooManyMatchesError, download_datasets


def test_download_stops_when_query_matches_more_than_five():
    with pytest.raises(TooManyMatchesError) as exc:
        download_datasets(usage_tag="control")

    assert exc.value.count > 5
    assert exc.value.dataset_uids
