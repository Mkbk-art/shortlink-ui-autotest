from __future__ import annotations

import ast
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
E2E = ROOT / "tests" / "e2e"

EXPECTED_WORKFLOWS = {
    "test_shortlink_lifecycle.py": "test_complete_shortlink_lifecycle",
    "test_group_link_isolation.py": "test_group_link_isolation",
    "test_link_identity.py": "test_short_url_identity_survives_edit",
    "test_recycle_ownership.py": "test_recovered_link_returns_to_original_group",
    "test_session_lifecycle.py": "test_logout_blocks_protected_route",
    "test_profile_persistence.py": "test_profile_mail_persists_across_relogin",
}


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _test_functions(path: Path) -> list[ast.FunctionDef]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]


def test_e2e_layer_contains_exact_six_cross_domain_workflows():
    assert E2E.is_dir()
    actual = {path.name for path in E2E.glob("test_*.py")}
    assert actual == set(EXPECTED_WORKFLOWS)
    for filename, test_name in EXPECTED_WORKFLOWS.items():
        tests = _test_functions(E2E / filename)
        assert [node.name for node in tests] == [test_name]


def test_e2e_marker_is_registered_and_applied():
    pytest_ini = _text("pytest.ini")
    assert "e2e: cross-domain end-to-end business workflow" in pytest_ini
    for filename in EXPECTED_WORKFLOWS:
        source = (E2E / filename).read_text(encoding="utf-8")
        assert "pytest.mark.e2e" in source
        assert "pytest.mark.ui" in source


def test_e2e_tests_use_page_objects_without_locator_or_sleep_leakage():
    forbidden = ("from selenium", "import selenium", "By.", "time.sleep", "driver.find_element")
    for filename in EXPECTED_WORKFLOWS:
        source = (E2E / filename).read_text(encoding="utf-8")
        for token in forbidden:
            assert token not in source, f"{filename} leaked implementation detail: {token}"


def test_home_page_exposes_real_logout_session_action():
    source = _text("page/home_page.py")
    tree = ast.parse(source)
    home = next(node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "HomePage")
    methods = {node.name for node in home.body if isinstance(node, ast.FunctionDef)}
    assert "logout" in methods
    assert "退出" in source
    assert "LoginPage" in source


def test_e2e_cleanup_fixture_tracks_resources_and_uses_ui_cleanup_only():
    source = _text("conftest.py")
    assert "def known_success_user(" in source
    assert "def e2e_cleanup(" in source
    assert "move_link_to_recycle" in source
    assert "permanently_delete_link" in source
    assert "delete_group" in source
    assert "requests." not in source
    assert "sqlite" not in source.lower()
    assert "mysql" not in source.lower()


def test_e2e_workflows_cover_distinct_cross_domain_invariants():
    lifecycle = _text("tests/e2e/test_shortlink_lifecycle.py")
    assert "create_group" in lifecycle
    assert "create_link" in lifecycle
    assert "edit_link" in lifecycle
    assert "open_short_link_and_get_final_url" in lifecycle
    assert "recover_link" in lifecycle
    assert "permanently_delete_link" in lifecycle
    assert ".logout()" in lifecycle

    isolation = _text("tests/e2e/test_group_link_isolation.py")
    assert isolation.count("create_group") >= 2
    assert isolation.count("create_link") >= 2
    assert "assert not" in isolation

    identity = _text("tests/e2e/test_link_identity.py")
    assert "short_url" in identity
    assert "edit_link" in identity
    assert "open_url_and_get_final_url" in identity

    ownership = _text("tests/e2e/test_recycle_ownership.py")
    assert "recover_link" in ownership
    assert ownership.count("select_group") >= 2

    session = _text("tests/e2e/test_session_lifecycle.py")
    assert ".logout()" in session
    assert "HOME_URL" in session
    assert "wait_until_loaded" in session

    profile = _text("tests/e2e/test_profile_persistence.py")
    assert "update_mail" in profile
    assert profile.count("login(") >= 2
    assert profile.count("logout()") >= 1


def test_ui_and_e2e_have_no_exact_duplicate_test_bodies_or_names():
    bodies = defaultdict(list)
    names = defaultdict(list)
    for root in (ROOT / "tests" / "ui", ROOT / "tests" / "e2e"):
        for path in root.rglob("test_*.py"):
            tree = ast.parse(path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                    continue
                normalized = ast.dump(ast.Module(body=node.body, type_ignores=[]), include_attributes=False)
                bodies[normalized].append(f"{path.relative_to(ROOT)}::{node.name}")
                names[node.name].append(str(path.relative_to(ROOT)))

    assert [locations for locations in bodies.values() if len(locations) > 1] == []
    assert {name: paths for name, paths in names.items() if len(paths) > 1} == {}
