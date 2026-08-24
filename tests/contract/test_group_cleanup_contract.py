from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    path = ROOT / relative
    assert path.exists(), f"missing group cleanup asset: {relative}"
    return path.read_text(encoding="utf-8")


def test_wait_group_absent_treats_stale_dom_as_transient_poll_state():
    source = _text("page/group_page.py")
    tree = ast.parse(source)

    assert "StaleElementReferenceException" in source

    group_page = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "GroupPage"
    )
    wait_method = next(
        node
        for node in group_page.body
        if isinstance(node, ast.FunctionDef) and node.name == "wait_group_absent"
    )

    catches_stale = False
    returns_false_on_stale = False
    for node in ast.walk(wait_method):
        if not isinstance(node, ast.Try):
            continue
        for handler in node.handlers:
            caught = handler.type
            if isinstance(caught, ast.Name) and caught.id == "StaleElementReferenceException":
                catches_stale = True
                returns_false_on_stale = any(
                    isinstance(child, ast.Return)
                    and isinstance(child.value, ast.Constant)
                    and child.value.value is False
                    for child in handler.body
                )

    assert catches_stale, "wait_group_absent must catch only stale DOM refreshes at the polling boundary"
    assert returns_false_on_stale, "a stale poll must return False so WebDriverWait re-queries the fresh DOM"


def test_group_cleanup_does_not_add_sleep_or_swallow_all_exceptions():
    source = _text("page/group_page.py")
    assert "time.sleep" not in source
    assert "except Exception" not in source


def test_group_dropdown_actions_follow_element_plus_hover_trigger():
    source = _text("page/group_page.py")
    tree = ast.parse(source)
    group_page = next(
        node for node in tree.body if isinstance(node, ast.ClassDef) and node.name == "GroupPage"
    )
    open_actions = next(
        node
        for node in group_page.body
        if isinstance(node, ast.FunctionDef) and node.name == "_open_group_actions"
    )
    method_source = ast.unparse(open_actions)

    assert "move_to_element(tool)" in method_source, (
        "Element Plus el-dropdown defaults to hover; group actions must hover the actual dropdown trigger"
    )
    assert "tool.click()" not in method_source, (
        "clicking a hover-triggered dropdown is timing-dependent and caused intermittent teardown failures"
    )
