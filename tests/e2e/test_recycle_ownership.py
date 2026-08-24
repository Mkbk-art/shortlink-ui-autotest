from __future__ import annotations

import pytest

from utils.test_data_factory import build_group_data, build_link_data

pytestmark = [pytest.mark.ui, pytest.mark.e2e]


def test_recovered_link_returns_to_original_group(driver, known_success_user, e2e_cleanup):
    from page.home_page import HomePage
    from page.link_page import LinkPage
    from page.login_page import LoginPage

    user = known_success_user
    LoginPage(driver).open().login(user["username"], user["password"], user.get("remember", False))
    group_page = HomePage(driver).wait_until_loaded().open_my_space()

    original_group = e2e_cleanup.track_group(build_group_data(prefix="e2e-own-a"))
    other_group = e2e_cleanup.track_group(build_group_data(prefix="e2e-own-b"))
    group_page.create_group(original_group.name)
    group_page.create_group(other_group.name)
    group_page.select_group(original_group.name)

    page = LinkPage(driver, timeout=group_page.timeout).wait_until_loaded()
    link = e2e_cleanup.track_link(original_group, build_link_data(prefix="e2e-own-link"))
    page.create_link(link.origin_url, link.description)
    short_url = page.get_link_record(link.description).short_url

    page.move_link_to_recycle(link.description)
    page.open_recycle_bin()
    page.recover_link(link.description)

    group_page.select_group(other_group.name)
    assert not page.has_link(link.description, timeout=1)
    group_page.select_group(original_group.name)
    page.wait_link_created(link.description, link.origin_url)
    assert page.has_link(link.description)
    restored_url = page.open_url_and_get_final_url(short_url)
    assert restored_url.rstrip("/") == link.origin_url.rstrip("/")

    page.move_link_to_recycle(link.description)
    page.open_recycle_bin()
    page.permanently_delete_link(link.description)
    e2e_cleanup.forget_link(link)

    group_page.select_group(other_group.name)
    group_page.delete_group(other_group.name)
    e2e_cleanup.forget_group(other_group)
    group_page.select_group(original_group.name)
    group_page.delete_group(original_group.name)
    e2e_cleanup.forget_group(original_group)
