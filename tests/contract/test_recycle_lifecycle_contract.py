from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RECYCLE_TEST = ROOT / "tests" / "ui" / "recycle" / "test_recycle_lifecycle.py"


def _text(relative: str) -> str:
    path = ROOT / relative
    assert path.exists(), f"missing recycle lifecycle asset: {relative}"
    return path.read_text(encoding="utf-8")


def _class_methods(relative: str, class_name: str) -> set[str]:
    tree = ast.parse(_text(relative))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return {
                child.name
                for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
    raise AssertionError(f"class {class_name} not found in {relative}")


def test_link_page_exposes_real_recycle_management_actions():
    methods = _class_methods("page/link_page.py", "LinkPage")
    assert {
        "open_recycle_bin",
        "move_link_to_recycle",
        "recover_link",
        "permanently_delete_link",
        "open_url_and_get_final_url",
    } <= methods

    source = _text("page/link_page.py")
    for stable_text in ["回收站", "是否移入回收站", "不可逆"]:
        assert stable_text in source
    assert "time.sleep" not in source
    assert "_wait_message_contains" not in source


def test_recycle_suite_covers_three_distinct_business_workflows():
    source = _text("tests/ui/recycle/test_recycle_lifecycle.py")
    tree = ast.parse(source)
    names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    }
    assert names == {
        "test_link_moves_to_recycle_and_appears_in_recycle_bin",
        "test_recycle_recover_restores_redirect_after_recycled_access",
        "test_recycle_permanent_delete_removes_link_and_disables_redirect",
    }
    for forbidden in [
        "selenium.webdriver",
        "By.",
        "find_element(",
        "execute_script",
        "requests.",
        "pymysql",
        "time.sleep",
    ]:
        assert forbidden not in source


def test_recycle_fixture_owns_cleanup_through_the_ui():
    source = _text("conftest.py")
    assert "temporary_recycle_link" in source
    assert "move_link_to_recycle" in source
    assert "open_recycle_bin" in source
    assert "permanently_delete_link" in source
    for forbidden in ["requests", "pymysql", "DELETE FROM", "UPDATE short_link"]:
        assert forbidden.lower() not in source.lower()
