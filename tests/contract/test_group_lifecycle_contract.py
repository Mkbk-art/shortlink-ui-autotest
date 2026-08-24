from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    path = ROOT / relative
    assert path.exists(), f"missing group lifecycle asset: {relative}"
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


def _load_data_factory_module():
    path = ROOT / "utils" / "test_data_factory.py"
    spec = importlib.util.spec_from_file_location("group_test_data_factory", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_group_page_encapsulates_group_dom_and_business_actions():
    methods = _class_methods("page/group_page.py", "GroupPage")
    assert {
        "wait_until_loaded",
        "create_group",
        "cancel_create_group",
        "rename_group",
        "delete_group",
        "has_group",
        "select_group",
        "is_group_selected",
        "get_group_names",
        "drag_group_onto",
        "create_blank_group",
        "delete_one_blank_group",
    } <= methods

    source = _text("page/group_page.py")
    for stable_selector in [".options-box", ".sortOptions", ".item-box", ".over-text", ".selectedItem"]:
        assert stable_selector in source
    assert "ActionChains" in source
    assert "time.sleep" not in source


def test_group_page_does_not_interpolate_group_names_into_xpath():
    source = _text("page/group_page.py")
    assert 'f"//' not in source
    assert "format(" not in source or "xpath" not in source.lower()
    assert ".over-text" in source


def test_home_page_exposes_my_space_group_entry():
    methods = _class_methods("page/home_page.py", "HomePage")
    assert "open_my_space" in methods
    source = _text("page/home_page.py")
    assert 'wait_url_contains("/home/space")' in source
    assert "GroupPage" in source


def test_group_fixtures_own_authenticated_group_and_ui_cleanup_lifecycle():
    source = _text("conftest.py")
    assert "authenticated_group_page" in source
    assert "temporary_group" in source
    assert "temporary_group_pair" in source
    assert "build_group_data" in source
    assert "delete_group" in source
    assert "login_data.json" in source
    assert "requests" not in source
    assert "pymysql" not in source.lower()


def test_group_suite_covers_exact_seven_business_scenarios_without_locator_leakage():
    source = _text("tests/ui/group/test_group_lifecycle.py")
    tree = ast.parse(source)
    names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    }
    assert names == {
        "test_group_create_and_select",
        "test_group_cancel_creation",
        "test_group_blank_name_is_allowed",
        "test_group_rename",
        "test_group_delete",
        "test_group_selection_switch",
        "test_group_drag_sort",
    }
    for forbidden in ["selenium.webdriver", "By.", "find_element(", "ActionChains", "time.sleep", "requests.", "pymysql"]:
        assert forbidden not in source
    assert "@pytest.mark.regression" in source


def test_blank_group_name_is_normal_business_behavior_with_delta_assertion_and_ui_cleanup():
    source = _text("tests/ui/group/test_group_lifecycle.py")
    assert "before = page.blank_group_count()" in source
    assert "create_blank_group" in source
    assert "before + 1" in source
    assert "delete_one_blank_group" in source
    assert "page.blank_group_count() == before" in source
    assert "pytest.fail" not in source
    assert "xfail" not in source


def test_blank_group_page_actions_sync_on_persistent_blank_count():
    create_source = _text("page/group_page.py")
    assert "def create_blank_group" in create_source
    assert "self.blank_group_count() == before + 1" in create_source

    delete_start = create_source.index("def delete_one_blank_group")
    delete_source = create_source[delete_start:]
    assert '_open_group_actions("")' in delete_source
    assert '_click_visible_dropdown_item("删除")' in delete_source
    assert "self.blank_group_count() == before - 1" in delete_source
    assert "_wait_message_any" not in delete_source


def test_generated_group_data_is_unique_short_and_mutable_for_cleanup_ownership():
    module = _load_data_factory_module()
    first = module.build_group_data()
    second = module.build_group_data()

    assert first.name != second.name
    assert first.name.startswith("ui-g-")
    assert len(first.name) <= 16
    old_name = first.name
    first.name = module.build_group_data(prefix="ui-r").name
    assert first.name != old_name
    assert first.active is True
    first.active = False
    assert first.active is False


def test_pytest_registers_group_regression_marker():
    source = _text("pytest.ini")
    assert "regression:" in source
