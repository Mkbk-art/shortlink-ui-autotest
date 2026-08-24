from __future__ import annotations

import pytest

pytestmark = pytest.mark.ui


class TestLink:
    def test_link_redirect_to_target(self, temporary_link):
        page = temporary_link.page
        link = temporary_link.link

        final_url = page.open_short_link_and_get_final_url(link.description)

        assert final_url.rstrip("/") == link.origin_url.rstrip("/")
