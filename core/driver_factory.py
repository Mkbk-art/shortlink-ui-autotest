from __future__ import annotations

from typing import Any

from config import (
    BROWSER,
    HEADLESS,
    PAGE_LOAD_TIMEOUT,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)


def _build_options(browser: str, headless: bool) -> Any:
    browser = browser.lower()
    if browser == "edge":
        from selenium.webdriver.edge.options import Options
    elif browser == "chrome":
        from selenium.webdriver.chrome.options import Options
    else:
        raise ValueError(f"不支持的浏览器: {browser}")

    options = Options()
    options.add_experimental_option("excludeSwitches", ["enable-logging"])
    options.add_argument("--disable-notifications")
    if headless:
        options.add_argument("--headless=new")
        options.add_argument(f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}")
    return options


def create_driver(browser: str | None = None, headless: bool | None = None):
    """Create a WebDriver with one explicit-wait strategy.

    Selenium Manager resolves the installed browser driver. The factory owns
    browser construction only; pytest fixtures own test lifecycle.
    """
    from selenium import webdriver

    selected_browser = (browser or BROWSER).lower()
    selected_headless = HEADLESS if headless is None else headless
    options = _build_options(selected_browser, selected_headless)

    if selected_browser == "edge":
        driver = webdriver.Edge(options=options)
    elif selected_browser == "chrome":
        driver = webdriver.Chrome(options=options)
    else:
        raise ValueError(f"不支持的浏览器: {selected_browser}")

    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    if not selected_headless:
        driver.maximize_window()
    return driver
