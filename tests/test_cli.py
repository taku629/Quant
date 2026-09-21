import json
from pathlib import Path

from quant_research.cli import main


def test_cli_writes_reproducible_computed_artifacts(tmp_path: Path) -> None:
    one = tmp_path / "one"
    two = tmp_path / "two"
    args = ["--seed", "19", "--periods", "15", "--strategy", "buy-hold"]
    assert main(["--output", str(one), *args]) == 0
    assert main(["--output", str(two), *args]) == 0
    assert (one / "summary.json").read_bytes() == (two / "summary.json").read_bytes()
    assert (one / "fills.csv").read_bytes() == (two / "fills.csv").read_bytes()
    summary = json.loads((one / "summary.json").read_text())
    assert summary["fill_count"] == 2
    assert summary["assumptions"].startswith("close signal")
