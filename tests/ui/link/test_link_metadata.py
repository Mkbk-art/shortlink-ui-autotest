from __future__ import annotations

import pytest

from utils.test_data_factory import build_link_data

pytestmark = pytest.mark.ui


class TestLink:
    def test_link_auto_fetches_description_from_origin_url(self, temporary_link_context):
        page = temporary_link_context.page
        candidate = build_link_data(prefix="ui-meta")

        page.open_create_dialog()
        description = page.enter_origin_and_wait_description(candidate.origin_url, timeout=15)

        assert description.strip()
        assert description != "Error while fetching title."
        page.close_create_dialog()

    def test_link_generated_short_url(self, temporary_link):
        record = temporary_link.page.get_link_record(temporary_link.link.description)

        assert record.short_url.startswith(("http://", "https://"))
        assert record.short_url != temporary_link.link.origin_url
