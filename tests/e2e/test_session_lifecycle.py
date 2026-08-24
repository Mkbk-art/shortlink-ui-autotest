from __future__ import annotations

import pytest

from config import HOME_URL

pytestmark = [pytest.mark.ui, pytest.mark.e2e]


def test_logout_blocks_protected_route(driver, known_success_user):
    from page.home_page import HomePage
    from page.login_page import LoginPage

    user = known_success_user
    LoginPage(driver).open().login(user["username"], user["password"], user.get("remember", False))
    home = HomePage(driver).wait_until_loaded()

    login_page = home.logout()
    assert login_page.is_login_form_visible()

    login_page.open_url(f"{HOME_URL}/space")
    login_page.wait_until_loaded()
    assert login_page.is_login_form_visible()
