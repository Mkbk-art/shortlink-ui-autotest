from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _load_module(relative: str, name: str):
    path = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_target_uses_real_metadata_site_and_keeps_override():
    source = _text("config.py")
    assert 'SHORTLINK_UI_TARGET_URL' in source
    assert 'https://nageoffer.com/' in source
    assert 'https://example.com/' not in source


def test_link_factory_keeps_real_target_unchanged_while_description_remains_unique(monkeypatch):
    monkeypatch.setenv("SHORTLINK_UI_TARGET_URL", "https://nageoffer.com/")
    module = _load_module("utils/test_data_factory.py", "link_metadata_test_data_factory")

    first = module.build_link_data()
    second = module.build_link_data()

    assert first.origin_url == "https://nageoffer.com/"
    assert second.origin_url == "https://nageoffer.com/"
    assert first.description != second.description
    assert "?ui=" not in first.origin_url


def test_create_form_primes_description_before_origin_to_avoid_title_overwrite():
    source = _text("page/link_page.py")
    assert "_fill_create_dialog_with_explicit_description" in source
    helper_start = source.index("def _fill_create_dialog_with_explicit_description")
    helper_end = source.index("\n    def ", helper_start + 5)
    helper = source[helper_start:helper_end]

    description_position = helper.index("_CREATE_DESCRIPTION_PLACEHOLDER")
    origin_position = helper.index("_CREATE_ORIGIN_PLACEHOLDER")
    assert description_position < origin_position


def test_link_page_exposes_real_title_autofill_observation_without_submitting():
    source = _text("page/link_page.py")
    assert "enter_origin_and_wait_description" in source
    assert "get_create_description_value" in source
    assert "Error while fetching title." in source


def test_metadata_and_editing_suites_keep_real_external_site_contracts():
    metadata_source = _text("tests/ui/link/test_link_metadata.py")
    metadata_tree = ast.parse(metadata_source)
    metadata_names = {
        node.name
        for node in ast.walk(metadata_tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
    }
    assert metadata_names == {
        "test_link_auto_fetches_description_from_origin_url",
        "test_link_generated_short_url",
    }

    editing_source = _text("tests/ui/link/test_link_editing.py")
    assert "https://www.cnblogs.com/" in editing_source
