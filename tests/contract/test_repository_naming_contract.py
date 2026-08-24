from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_contract_test_files_use_business_or_responsibility_names():
    legacy = []
    for path in sorted((ROOT / "tests").rglob("test_*.py")):
        if re.search(r"phase\d|fix\d", path.name, flags=re.IGNORECASE):
            legacy.append(path.name)
    assert legacy == [], f"legacy development-stage test names remain: {legacy}"


def test_contract_test_functions_do_not_encode_development_stage_names():
    legacy = []
    pattern = re.compile(r"def\s+(test_[^(]*(?:phase\d|fix\d)[^(]*)\(", re.IGNORECASE)
    for path in sorted((ROOT / "tests").rglob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        legacy.extend(f"{path.name}:{name}" for name in pattern.findall(text))
    assert legacy == [], f"legacy development-stage test names remain: {legacy}"


def test_legacy_script_test_tree_is_removed():
    assert not (ROOT / "script").exists()
