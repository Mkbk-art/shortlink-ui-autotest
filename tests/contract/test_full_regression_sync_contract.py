from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _method_source(relative: str, class_name: str, method_name: str) -> str:
    path = ROOT / relative
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return ast.get_source_segment(source, child) or ""
    raise AssertionError(f"method {class_name}.{method_name} not found in {relative}")


def test_non_empty_input_waits_for_final_value_not_transient_empty_state():
    source = _method_source("base/base_page.py", "BasePage", "input_text")

    # Clearing a field that will immediately receive text must not synchronize on
    # the transient empty DOM value. The durable postcondition is the requested
    # final value. Empty-input flows still need an explicit empty-value check.
    text_branch = source.index("if text:")
    empty_wait = source.index('get_attribute("value") == ""')
    assert text_branch < empty_wait, (
        "input_text still waits for an intermediate empty value before deciding "
        "whether the requested final value is non-empty"
    )
    assert 'get_attribute("value") == text' in source


def test_group_mutations_sync_on_persistent_list_state_not_success_toast():
    create_source = _method_source("page/group_page.py", "GroupPage", "create_group")
    rename_source = _method_source("page/group_page.py", "GroupPage", "rename_group")
    delete_source = _method_source("page/group_page.py", "GroupPage", "delete_group")

    assert "_wait_message_any" not in create_source
    assert "wait_group_present(group_name)" in create_source

    assert "_wait_message_any" not in rename_source
    assert "wait_group_present(new_name)" in rename_source
    assert "wait_group_absent(old_name)" in rename_source

    assert "_wait_message_any" not in delete_source
    assert "wait_group_absent(group_name)" in delete_source


def test_group_dialog_non_empty_replacement_waits_for_final_value_not_transient_empty_state():
    source = _method_source("page/group_page.py", "GroupPage", "_replace_dialog_input")

    text_branch = source.index("if text:")
    empty_wait = source.index('get_attribute("value") == ""')
    assert text_branch < empty_wait, (
        "group dialog replacement still waits for a transient empty value before "
        "deciding whether the requested final value is non-empty"
    )
    assert 'get_attribute("value") == text' in source
