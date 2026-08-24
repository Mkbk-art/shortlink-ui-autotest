from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


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


def test_base_page_exposes_page_level_explicit_sync_helpers():
    methods = _class_methods("base/base_page.py", "BasePage")
    assert "wait_elements_visible" in methods
    assert "wait_text_visible" in methods
    assert "wait_url_contains" in methods
    assert "wait_url_changes" in methods


def test_login_page_scopes_duplicate_inputs_to_visible_form_and_hides_locators():
    source = _text("page/login_page.py")
    assert ".logon:not(.hidden)" in source
    assert ".register:not(.hidden)" in source
    assert "_USERNAME_INPUT" in source
    assert "_PASSWORD_INPUT" in source
    assert "//label//span[@class='el-checkbox__inner']" not in source
    assert "@class='move'" not in source


def test_login_page_waits_for_page_state_after_open_and_form_switches():
    methods = _class_methods("page/login_page.py", "LoginPage")
    assert "wait_until_loaded" in methods
    source = _text("page/login_page.py")
    assert "self.wait_until_loaded()" in source
    assert "self.wait_register_form()" in source
    assert "self.wait_login_form()" in source


def test_home_page_has_composite_loaded_contract_and_display_name_rule():
    methods = _class_methods("page/home_page.py", "HomePage")
    assert "wait_until_loaded" in methods
    assert "expected_display_name" in methods

    source = _text("page/home_page.py")
    assert 'wait_url_contains("/home/")' in source
    assert "wait_element_visible(self._USER_NAME" in source
    assert 'username[:limit] + "..."' in source


def test_home_group_selection_does_not_build_xpath_from_test_data():
    source = _text("page/home_page.py")
    assert 'f"//div' not in source
    assert "wait_elements_visible(self._GROUP_LIST" in source
    assert "find_element(By.CSS_SELECTOR, \".over-text\")" in source


def test_login_tests_assert_business_state_instead_of_locator_or_weak_url_state():
    source = _text("tests/ui/authentication/test_login.py")
    assert "By." not in source
    assert "LOGIN_URL" not in source
    assert "REGISTER_SWITCH" not in source
    assert "LOGIN_SWITCH" not in source
    assert "current_url" not in source
    assert "home_page.wait_until_loaded()" in source
    assert "home_page.get_user_name()" in source
    assert "home_page.expected_display_name(username)" in source


def test_current_scope_exposes_account_and_excludes_unstable_statistics_ui():
    assert (ROOT / "tests" / "ui" / "recycle").is_dir()
    assert (ROOT / "tests" / "ui" / "account").is_dir()
    assert not (ROOT / "tests" / "ui" / "statistics").exists()
