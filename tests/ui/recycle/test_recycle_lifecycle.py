from __future__ import annotations

import pytest

pytestmark = pytest.mark.ui


class TestRecycleLifecycle:
    def test_link_moves_to_recycle_and_appears_in_recycle_bin(self, temporary_recycle_link):
        context = temporary_recycle_link
        page = context.page
        link = context.link

        page.move_link_to_recycle(link.description)
        link.active = False
        assert not page.has_link(link.description, timeout=1)

        page.open_recycle_bin()
        assert page.has_link(link.description)

    def test_recycle_recover_restores_redirect_after_recycled_access(self, temporary_recycle_link):
        context = temporary_recycle_link
        page = context.page
        link = context.link

        page.move_link_to_recycle(link.description)
        link.active = False
        page.open_recycle_bin()

        recycled_url = page.get_link_record(link.description).short_url
        unavailable_url = page.open_url_and_get_final_url(recycled_url)
        assert unavailable_url.rstrip("/").endswith("/page/notfound")

        page.recover_link(link.description)
        context.group_page.select_group(context.group.name)
        page.wait_link_created(link.description, link.origin_url)
        link.active = True

        final_url = page.open_short_link_and_get_final_url(link.description)
        assert final_url.rstrip("/") == link.origin_url.rstrip("/")

    def test_recycle_permanent_delete_removes_link_and_disables_redirect(self, temporary_recycle_link):
        context = temporary_recycle_link
        page = context.page
        link = context.link

        page.move_link_to_recycle(link.description)
        link.active = False
        page.open_recycle_bin()

        short_url = page.get_link_record(link.description).short_url
        page.permanently_delete_link(link.description)

        assert not page.has_link(link.description, timeout=1)
        final_url = page.open_url_and_get_final_url(short_url)
        assert final_url.rstrip("/").endswith("/page/notfound")
