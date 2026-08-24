from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    path = ROOT / relative
    assert path.exists(), f"missing Statistics/Account asset: {relative}"
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


def _test_names(relative: str) -> set[str]:
    tree = ast.parse(_text(relative))
    return {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    }


def test_statistics_ui_is_intentionally_excluded_from_stable_regression_suite():
    assert not (ROOT / "page" / "statistics_page.py").exists()
    assert not (ROOT / "tests" / "ui" / "statistics").exists()
    link_source = _text("page/link_page.py")
    assert "def open_statistics(" not in link_source
    assert "StatisticsPage" not in link_source


def test_home_and_account_pages_encapsulate_profile_navigation_and_editing():
    home_methods = _class_methods("page/home_page.py", "HomePage")
    account_methods = _class_methods("page/account_page.py", "AccountPage")
    assert "open_account" in home_methods
    assert {
        "wait_until_loaded",
        "get_profile",
        "update_mail",
        "close_edit_dialog_if_open",
    } <= account_methods

    home_source = _text("page/home_page.py")
    assert "ActionChains" in home_source
    assert "个人信息" in home_source
    assert "move_to_element" in home_source

    account_source = _text("page/account_page.py")
    assert "修改个人信息" in account_source
    assert "请输入邮箱" in account_source
    assert "默认密码" not in account_source
    assert "time.sleep" not in account_source


def test_account_fixture_restores_original_profile_through_ui():
    source = _text("conftest.py")
    assert "account_profile_context" in source
    assert "original_profile" in source
    assert "close_edit_dialog_if_open()" in source
    assert "update_mail(original_profile.mail)" in source
    for forbidden in ["requests", "pymysql", "DELETE FROM", "UPDATE "]:
        assert forbidden.lower() not in source.lower()


def test_account_suite_keeps_one_reversible_profile_workflow_without_password_scope():
    relative = "tests/ui/account/test_account_profile.py"
    source = _text(relative)
    assert _test_names(relative) == {"test_account_profile_mail_update_and_restore"}
    assert "build_profile_mail" in source
    assert "update_mail" in source
    assert "@pytest.mark.xfail" not in source
    assert "password" not in source.lower()
    assert "empty_real_name" not in source
    for forbidden in ["selenium.webdriver", "By.", "find_element(", "time.sleep", "requests."]:
        assert forbidden not in source


def test_profile_test_data_builds_unique_valid_mail():
    source = _text("utils/test_data_factory.py")
    assert "def build_profile_mail" in source
    assert "@test.com" in source
