from __future__ import annotations

import pytest

from utils.test_data_factory import build_profile_mail

pytestmark = [pytest.mark.ui, pytest.mark.e2e]


def test_profile_mail_persists_across_relogin(driver, known_success_user, e2e_cleanup):
    from page.home_page import HomePage
    from page.login_page import LoginPage

    user = known_success_user
    LoginPage(driver).open().login(user["username"], user["password"], user.get("remember", False))
    home = HomePage(driver).wait_until_loaded()
    account = home.open_account()
    original = account.get_profile()
    replacement_mail = build_profile_mail()
    e2e_cleanup.track_profile_mail(original.mail)

    account.update_mail(replacement_mail)
    assert account.get_profile().mail == replacement_mail

    login_page = HomePage(driver).logout()
    login_page.login(user["username"], user["password"], user.get("remember", False))
    account_after_login = HomePage(driver).wait_until_loaded().open_account()
    assert account_after_login.get_profile().mail == replacement_mail

    account_after_login.update_mail(original.mail)
    assert account_after_login.get_profile().mail == original.mail
    e2e_cleanup.clear_profile_mail()
