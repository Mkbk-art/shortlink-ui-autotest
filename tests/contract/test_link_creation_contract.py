from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _source(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _method_source(relative: str, class_name: str, method_name: str) -> str:
    source = _source(relative)
    tree = ast.parse(source)
    lines = source.splitlines()
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    assert child.end_lineno is not None
                    return "\n".join(lines[child.lineno - 1 : child.end_lineno])
    raise AssertionError(f"missing {class_name}.{method_name}")


def test_create_link_uses_business_postcondition_not_success_toast():
    method = _method_source("page/link_page.py", "LinkPage", "create_link")

    assert "_wait_message_contains" not in method
    assert "_wait_dialog_hidden" in method
    assert "wait_link_created" in method


def test_link_creation_postcondition_requires_origin_and_generated_short_url():
    method = _method_source("page/link_page.py", "LinkPage", "wait_link_created")

    assert "_link_record_if_present" in method
    assert "record.short_url" in method
    assert "record.origin_url" in method
    assert "origin_url" in method
    assert "WebDriverWait" in method


def test_link_row_actions_are_scoped_to_operation_column():
    source = _source("page/link_page.py")

    assert '_ROW_ACTION_BUTTONS = "td:last-child .table-edit"' in source
    assert "_row_action_button(row, 1)" in source
    assert "_row_action_button(row, 2)" in source


def test_link_record_reads_origin_from_dedicated_url_element_not_row_text():
    source = _source("page/link_page.py")
    method = _method_source("page/link_page.py", "LinkPage", "_record_from_row")

    assert '_ROW_ORIGIN_URL = ".table-url-box > span"' in source
    assert "row.find_element(By.CSS_SELECTOR, self._ROW_ORIGIN_URL)" in method
    assert "row.text.splitlines()" not in source


def test_link_creation_wait_polls_fresh_rows_without_nested_full_waits():
    method = _method_source("page/link_page.py", "LinkPage", "wait_link_created")

    assert "_link_record_if_present" in method
    assert "get_link_record(description)" not in method


def test_origin_url_locator_excludes_generated_short_link_inner_span():
    source = _source("page/link_page.py")

    assert '_ROW_ORIGIN_URL = ".table-url-box > span"' in source
    assert '_ROW_ORIGIN_URL = ".table-url-box span"' not in source


def test_link_creation_timeout_reports_business_state_diagnostics():
    source = _source("page/link_page.py")
    method = _method_source("page/link_page.py", "LinkPage", "wait_link_created")

    assert '_SELECTED_GROUP_NAME = ".sortOptions .item-box.selectedItem .over-text"' in source
    assert "_link_creation_diagnostics" in source
    assert "except TimeoutException" in method
    for field in [
        "descriptions",
        "matched_row",
        "actual_origin_url",
        "actual_short_url",
        "selected_group",
    ]:
        assert field in source
