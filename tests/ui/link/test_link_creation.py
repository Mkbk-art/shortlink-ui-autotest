from __future__ import annotations

import pytest

from utils.test_data_factory import build_link_data

pytestmark = pytest.mark.ui


class TestLink:
    def test_link_create_and_list_visibility(self, temporary_link):
        page = temporary_link.page
        link = temporary_link.link

        assert page.has_link(link.description)

    def test_link_blank_origin_url_validation(self, temporary_link_context):
        page = temporary_link_context.page
        candidate = build_link_data(prefix="ui-valid")

        page.submit_create_form("", candidate.description)
        assert "请输入链接" in page.get_create_validation_messages()
        page.close_create_dialog()
        assert not page.has_link(candidate.description, timeout=1)

    def test_link_cancel_creation(self, temporary_link_context):
        page = temporary_link_context.page
        candidate = build_link_data(prefix="ui-cancel")
        before = page.get_link_count()

        page.cancel_create_link(candidate.origin_url, candidate.description)

        assert page.get_link_count() == before
        assert not page.has_link(candidate.description, timeout=1)
