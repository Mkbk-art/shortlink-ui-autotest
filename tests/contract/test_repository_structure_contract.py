import ast
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_tests_are_separated_by_execution_type_and_business_domain():
    assert not (ROOT / "script").exists()
    assert (ROOT / "tests" / "contract").is_dir()
    assert (ROOT / "tests" / "e2e").is_dir()
    assert (ROOT / "tests" / "ui" / "authentication").is_dir()
    assert (ROOT / "tests" / "ui" / "group").is_dir()
    assert (ROOT / "tests" / "ui" / "link").is_dir()
    assert (ROOT / "tests" / "ui" / "recycle").is_dir()
    assert not (ROOT / "tests" / "ui" / "statistics").exists()
    assert (ROOT / "tests" / "ui" / "account").is_dir()


def test_pytest_collects_only_from_tests_tree():
    source = (ROOT / "pytest.ini").read_text(encoding="utf-8")
    assert "testpaths = tests" in source
    assert "testpaths = script tests" not in source


def test_ui_tests_have_no_exact_duplicate_cases():
    bodies = defaultdict(list)
    names = defaultdict(list)
    for path in (ROOT / "tests" / "ui").rglob("test_*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test_"):
                continue
            normalized = ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False)
            bodies[normalized].append(f"{path.relative_to(ROOT)}::{node.name}")
            names[node.name].append(str(path.relative_to(ROOT)))

    duplicate_bodies = [locations for locations in bodies.values() if len(locations) > 1]
    duplicate_names = {name: paths for name, paths in names.items() if len(paths) > 1}
    assert duplicate_bodies == []
    assert duplicate_names == {}
