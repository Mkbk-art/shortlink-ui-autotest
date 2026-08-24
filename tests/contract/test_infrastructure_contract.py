from __future__ import annotations

import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_driver_factory_is_separated_from_legacy_tools():
    factory = ROOT / "core" / "driver_factory.py"
    assert factory.exists(), "Infrastructure should provide core/driver_factory.py"

    tools_source = _text("tools.py")
    assert "from selenium import webdriver" not in tools_source
    assert "def get_driver" not in tools_source


def test_driver_factory_uses_explicit_wait_strategy_only():
    source = _text("core/driver_factory.py")
    assert ".implicitly_wait(" not in source
    assert "set_page_load_timeout" in source


def test_root_conftest_owns_driver_lifecycle_and_failure_screenshot():
    source = _text("conftest.py")
    assert "def driver(" in source
    assert "yield driver" in source
    assert ".quit()" in source
    assert "pytest_runtest_makereport" in source
    assert "get_screenshot_as_png" in source
    assert "allure.attach" in source


def test_login_tests_use_fixtures_without_sleep_or_manual_driver_lifecycle():
    source = _text("tests/ui/authentication/test_login.py")
    assert "setup_method" not in source
    assert "teardown_method" not in source
    assert "time.sleep" not in source
    assert "get_driver" not in source
    assert "login_page" in source
    assert "home_page" in source


def test_input_logging_does_not_emit_typed_value():
    source = _text("base/base_page.py")
    assert "-> {text}" not in source


def test_runtime_settings_can_be_overridden_by_environment(monkeypatch):
    monkeypatch.setenv("SHORTLINK_UI_BASE_URL", "http://127.0.0.1:9999/")
    monkeypatch.setenv("SHORTLINK_UI_BROWSER", "chrome")
    monkeypatch.setenv("SHORTLINK_UI_HEADLESS", "true")
    monkeypatch.setenv("SHORTLINK_UI_EXPLICIT_WAIT", "6")

    import config

    reloaded = importlib.reload(config)
    assert reloaded.BASE_URL == "http://127.0.0.1:9999"
    assert reloaded.LOGIN_URL == "http://127.0.0.1:9999/login"
    assert reloaded.BROWSER == "chrome"
    assert reloaded.HEADLESS is True
    assert reloaded.EXPLICITLY_WAIT == 6

    monkeypatch.delenv("SHORTLINK_UI_BASE_URL", raising=False)
    monkeypatch.delenv("SHORTLINK_UI_BROWSER", raising=False)
    monkeypatch.delenv("SHORTLINK_UI_HEADLESS", raising=False)
    monkeypatch.delenv("SHORTLINK_UI_EXPLICIT_WAIT", raising=False)
    importlib.reload(config)


def test_pytest_collects_from_canonical_tests_tree():
    source = _text("pytest.ini")
    assert "testpaths = tests" in source
    assert "testpaths = script tests" not in source
