from __future__ import annotations

import pytest

from utils.test_data_factory import build_link_data

pytestmark = pytest.mark.ui


class TestLink:
    def test_link_edit_origin_url(self, temporary_link):
        page = temporary_link.page
        link = temporary_link.link
        edited = build_link_data(target_url="https://www.cnblogs.com/", prefix="ui-url")

        page.edit_link(link.description, origin_url=edited.origin_url)
        link.origin_url = edited.origin_url

        assert page.get_link_record(link.description).origin_url == link.origin_url

    def test_link_edit_description(self, temporary_link):
        page = temporary_link.page
        link = temporary_link.link
        old_description = link.description
        new_description = build_link_data(prefix="ui-edit").description

        page.edit_link(old_description, new_description=new_description)
        link.description = new_description

        assert page.has_link(new_description)
        assert not page.has_link(old_description, timeout=1)
