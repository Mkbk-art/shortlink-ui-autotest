from __future__ import annotations

import pytest

from utils.test_data_factory import build_group_data, build_link_data

pytestmark = [pytest.mark.ui, pytest.mark.e2e]


def test_group_link_isolation(driver, known_success_user, e2e_cleanup):
    from page.home_page import HomePage
    from page.link_page import LinkPage
    from page.login_page import LoginPage

    user = known_success_user
    LoginPage(driver).open().login(user["username"], user["password"], user.get("remember", False))
    group_page = HomePage(driver).wait_until_loaded().open_my_space()

    group_a = e2e_cleanup.track_group(build_group_data(prefix="e2e-iso-a"))
    group_b = e2e_cleanup.track_group(build_group_data(prefix="e2e-iso-b"))
    group_page.create_group(group_a.name)
    group_page.create_group(group_b.name)

    page = LinkPage(driver, timeout=group_page.timeout)
    group_page.select_group(group_a.name)
    page.wait_until_loaded()
    link_a = e2e_cleanup.track_link(group_a, build_link_data(prefix="e2e-iso-link-a"))
    page.create_link(link_a.origin_url, link_a.description)

    group_page.select_group(group_b.name)
    page.wait_until_loaded()
    link_b = e2e_cleanup.track_link(group_b, build_link_data(prefix="e2e-iso-link-b"))
    page.create_link(link_b.origin_url, link_b.description)
    assert page.has_link(link_b.description)
    assert not page.has_link(link_a.description, timeout=1)

    group_page.select_group(group_a.name)
    assert page.has_link(link_a.description)
    assert not page.has_link(link_b.description, timeout=1)

    page.move_link_to_recycle(link_a.description)
    group_page.select_group(group_b.name)
    page.move_link_to_recycle(link_b.description)
    page.open_recycle_bin()
    page.permanently_delete_link(link_a.description)
    page.permanently_delete_link(link_b.description)
    e2e_cleanup.forget_link(link_a)
    e2e_cleanup.forget_link(link_b)

    group_page.select_group(group_b.name)
    group_page.delete_group(group_b.name)
    e2e_cleanup.forget_group(group_b)
    group_page.select_group(group_a.name)
    group_page.delete_group(group_a.name)
    e2e_cleanup.forget_group(group_a)
