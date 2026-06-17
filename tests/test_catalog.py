import pytest

from scmora_db.catalog import (
    list_usage_tags,
    list_values,
    resolve_matches,
    search_datasets,
)
from scmora_db.exceptions import TooManyMatchesError


def test_search_by_dataset_id():
    df = search_datasets(dataset_id="GSM5085810_GM12878_rep1")

    assert len(df) == 1
    assert df.loc[0, "dataset_uid"] == "GSE166797/GSM5085810_GM12878_rep1"
    assert df.loc[0, "file_path"] == "GSE166797/GSM5085810_GM12878_rep1.h5mu"


def test_search_by_usage_tag():
    df = search_datasets(usage_tag="control")

    assert not df.empty
    assert all("control" in value.split(";") for value in df["usage_tags"])


def test_resolve_raises_for_more_than_five():
    with pytest.raises(TooManyMatchesError) as exc:
        resolve_matches(usage_tag="control")

    assert exc.value.count > 5
    assert exc.value.dataset_uids


def test_list_usage_tags_contains_expected_tags():
    tags = list_usage_tags()

    assert "model_training" in tags
    assert "control" in tags


def test_list_values_for_common_filter_fields():
    assert "Healthy/Control" in list_values("condition")
    assert "GSE166797" in list_values("gse-ids")
    assert "GM12878 (Cell Line)" in list_values("detail-sources")
    assert "model_training" in list_values("groups")
