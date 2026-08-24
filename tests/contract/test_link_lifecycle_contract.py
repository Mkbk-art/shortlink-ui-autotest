from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    path = ROOT / relative
    assert path.exists(), f"missing link lifecycle asset: {relative}"
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


def _load_module(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_link_page_encapsulates_create_read_edit_redirect_and_cleanup_actions():
    methods = _class_methods("page/link_page.py", "LinkPage")
    assert {
        "wait_until_loaded",
        "open_create_dialog",
        "create_link",
        "cancel_create_link",
        "get_create_validation_messages",
        "has_link",
        "get_link_record",
        "get_link_count",
        "edit_link",
        "open_short_link_and_get_final_url",
        "move_link_to_recycle",
    } <= methods

    source = _text("page/link_page.py")
    for stable_text in [
        "创建短链",
        "创建链接",
        "编辑链接",
        "请输入http://或https://开头的链接或应用跳转链接",
        "请输入描述信息",
        "table-link-box",
        "fullShortUrl",
    ]:
        assert stable_text in source
    assert "time.sleep" not in source


def test_link_page_does_not_build_xpath_from_dynamic_link_data():
    source = _text("page/link_page.py")
    assert 'f"//' not in source
    assert "origin_url}" not in source
    assert "description}" not in source
    assert "_find_row" in source


def test_link_fixtures_own_group_link_and_ui_cleanup_lifecycle():
    source = _text("conftest.py")
    assert "temporary_link_context" in source
    assert "temporary_link" in source
    assert "build_group_data" in source
    assert "build_link_data" in source
    assert "create_group" in source
    assert "select_group" in source
    assert "move_link_to_recycle" in source
    assert "delete_group" in source
    for forbidden in ["requests", "pymysql", "DELETE FROM", "INSERT INTO"]:
        assert forbidden.lower() not in source.lower()


def test_link_ui_suites_are_split_by_business_responsibility_without_locator_leakage():
    expected = {
        "tests/ui/link/test_link_creation.py": {
            "test_link_create_and_list_visibility",
            "test_link_blank_origin_url_validation",
            "test_link_cancel_creation",
        },
        "tests/ui/link/test_link_metadata.py": {
            "test_link_auto_fetches_description_from_origin_url",
            "test_link_generated_short_url",
        },
        "tests/ui/link/test_link_editing.py": {
            "test_link_edit_origin_url",
            "test_link_edit_description",
        },
        "tests/ui/link/test_link_redirect.py": {
            "test_link_redirect_to_target",
        },
    }

    for relative, expected_names in expected.items():
        source = _text(relative)
        tree = ast.parse(source)
        names = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name.startswith("test_")
        }
        assert names == expected_names
        for forbidden in [
            "selenium.webdriver",
            "By.",
            "find_element(",
            "ActionChains",
            "time.sleep",
            "requests.",
            "pymysql",
        ]:
            assert forbidden not in source


def test_generated_link_data_is_unique_and_supports_mutable_cleanup_ownership():
    module = _load_module("utils/test_data_factory.py", "link_test_data_factory")
    first = module.build_link_data()
    second = module.build_link_data()

    assert first.description != second.description
    assert first.description.startswith("ui-link-")
    assert first.origin_url.startswith("https://")
    assert first.active is True
    first.origin_url = "https://www.cnblogs.com/"
    first.description = "ui-edit-description"
    assert first.origin_url == "https://www.cnblogs.com/"
    assert first.description == "ui-edit-description"
    first.active = False
    assert first.active is False


def test_config_exposes_overridable_target_url():
    source = _text("config.py")
    assert "SHORTLINK_UI_TARGET_URL" in source
    assert "https://nageoffer.com/" in source
    assert "TARGET_URL" in source


def test_link_scope_keeps_recycle_separate_and_excludes_statistics_regression():
    assert not (ROOT / "tests" / "ui" / "link" / "test_link_recycle_transition.py").exists()
    assert (ROOT / "tests" / "ui" / "recycle" / "test_recycle_lifecycle.py").exists()
    assert not (ROOT / "tests" / "ui" / "statistics").exists()
    assert not (ROOT / "page" / "statistics_page.py").exists()
    assert "def open_statistics(" not in _text("page/link_page.py")
