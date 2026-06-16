import pytest


pytest.importorskip("huggingface_hub")
pytest.importorskip("mudata")

from scmora_db.cli import main


def test_cli_search(capsys):
    code = main(["search", "--dataset-id", "GSM5085810_GM12878_rep1"])

    captured = capsys.readouterr()
    assert code == 0
    assert "GSE166797/GSM5085810_GM12878_rep1" in captured.out


def test_cli_list_usage_tags(capsys):
    code = main(["list", "usage-tags"])

    captured = capsys.readouterr()
    assert code == 0
    assert "control" in captured.out
