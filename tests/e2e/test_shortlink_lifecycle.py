from __future__ import annotations

import pytest

from utils.test_data_factory import build_group_data, build_link_data

pytestmark = [pytest.mark.ui, pytest.mark.e2e]


def test_complete_shortlink_lifecycle(driver, known_success_user, e2e_cleanup):
    from page.home_page import HomePage
    from page.link_page import LinkPage
    from page.login_page import LoginPage

    user = known_success_user
    LoginPage(driver).open().login(user["username"], user["password"], user.get("remember", False))
    home = HomePage(driver).wait_until_loaded()
    group_page = home.open_my_space()

    group = e2e_cleanup.track_group(build_group_data(prefix="e2e-life-g"))
    group_page.create_group(group.name)
    group_page.select_group(group.name)

    page = LinkPage(driver, timeout=group_page.timeout).wait_until_loaded()
    link = e2e_cleanup.track_link(group, build_link_data(prefix="e2e-life-link"))
    page.create_link(link.origin_url, link.description)
    assert page.get_link_record(link.description).origin_url.rstrip("/") == link.origin_url.rstrip("/")

    edited_description = build_link_data(prefix="e2e-life-edit").description
    page.edit_link(link.description, new_description=edited_description)
    link.description = edited_description
    short_url = page.get_link_record(link.description).short_url

    final_url = page.open_short_link_and_get_final_url(link.description)
    assert final_url.rstrip("/") == link.origin_url.rstrip("/")

    page.move_link_to_recycle(link.description)
    page.open_recycle_bin()
    unavailable_url = page.open_url_and_get_final_url(short_url)
    assert unavailable_url.rstrip("/").endswith("/page/notfound")

    page.recover_link(link.description)
    group_page.select_group(group.name)
    page.wait_link_created(link.description, link.origin_url)
    restored_url = page.open_short_link_and_get_final_url(link.description)
    assert restored_url.rstrip("/") == link.origin_url.rstrip("/")

    page.move_link_to_recycle(link.description)
    page.open_recycle_bin()
    page.permanently_delete_link(link.description)
    e2e_cleanup.forget_link(link)

    group_page.select_group(group.name)
    group_page.delete_group(group.name)
    e2e_cleanup.forget_group(group)

    login_page = HomePage(driver).logout()
    assert login_page.is_login_form_visible()
