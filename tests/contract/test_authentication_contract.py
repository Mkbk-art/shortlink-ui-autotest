from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    path = ROOT / relative
    assert path.exists(), f"missing authentication asset: {relative}"
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
    assert path.exists(), "Authentication coverage must provide a reusable UI test-data factory"
    spec = importlib.util.spec_from_file_location("authentication_test_data_factory", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_login_page_exposes_business_level_login_validation_and_message_api():
    methods = _class_methods("page/login_page.py", "LoginPage")
    assert {
        "submit_login",
        "get_login_validation_messages",
        "wait_message",
    } <= methods


def test_login_page_supports_registration_without_exposing_locators_to_tests():
    methods = _class_methods("page/login_page.py", "LoginPage")
    assert {
        "register",
        "submit_register",
        "get_register_validation_messages",
    } <= methods

    source = _text("page/login_page.py")
    for placeholder in ["请输入邮箱", "请输入手机号", "请输入姓名"]:
        assert placeholder in source
    assert ".register:not(.hidden)" in source


def test_authentication_scripts_are_split_and_do_not_use_selenium_locators_directly():
    login_source = _text("tests/ui/authentication/test_login.py")
    register_source = _text("tests/ui/authentication/test_register.py")

    for source in (login_source, register_source):
        assert "selenium.webdriver" not in source
        assert "By." not in source
        assert "find_element(" not in source

    assert "get_login_validation_messages" in login_source
    assert "get_register_validation_messages" in register_source


def test_login_suite_covers_success_server_rejection_and_frontend_validation():
    source = _text("tests/ui/authentication/test_login.py")
    expected_names = {
        "test_login_success",
        "test_login_wrong_password",
        "test_login_unknown_user",
        "test_login_empty_password_validation",
        "test_login_short_password_validation",
        "test_login_empty_username_known_validation_defect",
    }
    tree = ast.parse(source)
    names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert expected_names <= names
    assert "xfail" in source


def test_register_suite_covers_validation_existing_user_success_and_known_real_name_defect():
    source = _text("tests/ui/authentication/test_register.py")
    expected_names = {
        "test_register_required_fields_validation",
        "test_register_invalid_email_validation",
        "test_register_invalid_phone_validation",
        "test_register_short_password_validation",
        "test_register_existing_username",
        "test_register_success_with_unique_user",
        "test_register_empty_real_name_known_validation_defect",
    }
    tree = ast.parse(source)
    names = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert expected_names <= names
    assert "persistent_data" in source
    assert "xfail" in source


def test_generated_registration_data_is_unique_and_respects_frontend_constraints():
    module = _load_data_factory_module()
    first = module.build_registration_data()
    second = module.build_registration_data()

    assert first.username != second.username
    assert len(first.username) <= 11
    assert first.username.startswith("ui")
    assert len(first.phone) == 11
    assert first.phone.startswith(("13", "15", "17", "18", "19"))
    assert "@" in first.mail
    assert 8 <= len(first.password) <= 15
    assert first.real_name


def test_pytest_registers_persistent_data_marker():
    source = _text("pytest.ini")
    assert "persistent_data:" in source
