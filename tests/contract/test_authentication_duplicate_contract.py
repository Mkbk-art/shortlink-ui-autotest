from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    path = ROOT / relative
    assert path.exists(), f"missing authentication duplicate-validation asset: {relative}"
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


def test_login_page_can_wait_for_any_allowed_business_message():
    source = _text("page/login_page.py")
    tree = ast.parse(source)
    methods = {
        child.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "LoginPage"
        for child in node.body
        if isinstance(child, ast.FunctionDef)
    }

    assert "wait_message_any" in methods


def test_existing_username_accepts_both_duplicate_rejection_paths_and_stays_on_register():
    source = _method_source(
        "tests/ui/authentication/test_register.py", "TestRegister", "test_register_existing_username"
    )

    assert '"用户名已存在"' in source
    assert '"用户记录已存在"' in source
    assert "wait_message_any" in source
    assert "is_register_form_visible" in source
    assert 'wait_message_contains("用户名已存在")' not in source
