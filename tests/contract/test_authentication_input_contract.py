from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    path = ROOT / relative
    assert path.exists(), f"missing authentication input-validation asset: {relative}"
    return path.read_text(encoding="utf-8")


def _method_source(relative: str, class_name: str, method_name: str) -> str:
    source = _text(relative)
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            for child in node.body:
                if isinstance(child, ast.FunctionDef) and child.name == method_name:
                    return ast.get_source_segment(source, child) or ""
    raise AssertionError(f"method {class_name}.{method_name} not found in {relative}")


def test_empty_input_uses_real_keyboard_clear_confirms_value_and_blurs():
    source = _method_source("base/base_page.py", "BasePage", "input_text")

    assert "Keys.CONTROL" in source
    assert "Keys.BACKSPACE" in source
    assert 'get_attribute("value")' in source or "get_attribute('value')" in source
    assert "Keys.TAB" in source
    assert "element.clear()" not in source


def test_login_page_exposes_semantic_message_contains_wait():
    source = _text("page/login_page.py")
    tree = ast.parse(source)
    methods = {
        child.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LoginPage"
        for child in node.body
        if isinstance(child, ast.FunctionDef)
    }

    assert "wait_message_contains" in methods


def test_existing_username_case_matches_backend_message_without_punctuation_contract():
    source = _method_source(
        "tests/ui/authentication/test_register.py", "TestRegister", "test_register_existing_username"
    )

    assert '"用户名已存在"' in source
    assert "wait_message_any" in source
    assert "用户名已存在！" not in source
