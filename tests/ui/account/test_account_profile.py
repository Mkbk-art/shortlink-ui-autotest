from __future__ import annotations

import pytest

from utils.test_data_factory import build_profile_mail

pytestmark = pytest.mark.ui


class TestAccountProfile:
    def test_account_profile_mail_update_and_restore(self, account_profile_context):
        context = account_profile_context
        page = context.page
        original = context.original_profile
        replacement_mail = build_profile_mail()

        assert original.username
        assert original.phone
        assert original.real_name
        assert original.mail

        page.update_mail(replacement_mail)
        updated = page.get_profile()
        assert updated.mail == replacement_mail
        assert updated.username == original.username
        assert updated.phone == original.phone
        assert updated.real_name == original.real_name

        page.update_mail(original.mail)
        context.restored = True
        assert page.get_profile() == original
