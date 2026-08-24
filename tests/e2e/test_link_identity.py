from __future__ import annotations

import pytest

from utils.test_data_factory import build_group_data, build_link_data

pytestmark = [pytest.mark.ui, pytest.mark.e2e]


def test_short_url_identity_survives_edit(driver, known_success_user, e2e_cleanup):
    from page.home_page import HomePage
    from page.link_page import LinkPage
    from page.login_page import LoginPage

    user = known_success_user
    LoginPage(driver).open().login(user["username"], user["password"], user.get("remember", False))
    group_page = HomePage(driver).wait_until_loaded().open_my_space()

    group = e2e_cleanup.track_group(build_group_data(prefix="e2e-id-g"))
    group_page.create_group(group.name)
    group_page.select_group(group.name)
    page = LinkPage(driver, timeout=group_page.timeout).wait_until_loaded()

    link = e2e_cleanup.track_link(group, build_link_data(prefix="e2e-id-link"))
    page.create_link(link.origin_url, link.description)
    before = page.get_link_record(link.description)

    edited = build_link_data(target_url="https://www.cnblogs.com/", prefix="e2e-id-edit")
    page.edit_link(
        link.description,
        origin_url=edited.origin_url,
        new_description=edited.description,
    )
    link.origin_url = edited.origin_url
    link.description = edited.description

    after = page.get_link_record(link.description)
    assert after.short_url == before.short_url
    assert after.origin_url.rstrip("/") == link.origin_url.rstrip("/")
    final_url = page.open_url_and_get_final_url(before.short_url)
    assert final_url.rstrip("/") == link.origin_url.rstrip("/")

    page.move_link_to_recycle(link.description)
    page.open_recycle_bin()
    page.permanently_delete_link(link.description)
    e2e_cleanup.forget_link(link)
    group_page.select_group(group.name)
    group_page.delete_group(group.name)
    e2e_cleanup.forget_group(group)
