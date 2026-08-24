from __future__ import annotations

import pytest

from tools import get_logger, read_json_data
from utils.test_data_factory import build_registration_data

logger = get_logger()


def _load_login_cases():
    try:
        return read_json_data("login_data.json")
    except FileNotFoundError:
        logger.warning("未找到本地 login_data.json，需要真实账号的登录用例将跳过")
        return []


def _known_user() -> dict | None:
    for case in _load_login_cases():
        if case.get("expected") == "success" and case.get("username") and case.get("password"):
            return case
    return None


@pytest.fixture(scope="module")
def known_user():
    user = _known_user()
    if user is None:
        pytest.skip("本地 login_data.json 中没有 expected=success 的真实账号")
    return user


@pytest.mark.ui
class TestLogin:
    """登录模块：正常路径、服务端拒绝和前端表单校验。"""

    def test_login_success(self, login_page, home_page, known_user):
        username = known_user["username"]
        login_page.login(
            username,
            known_user["password"],
            known_user.get("remember", False),
        )

        home_page.wait_until_loaded()
        assert home_page.get_user_name() == home_page.expected_display_name(username)

    def test_login_wrong_password(self, login_page, known_user):
        login_page.login(known_user["username"], "Wrong123!")

        assert login_page.wait_message("请输入正确的账号密码!") == "请输入正确的账号密码!"
        assert login_page.is_login_form_visible()

    def test_login_unknown_user(self, login_page):
        unknown = build_registration_data().username
        login_page.login(unknown, "UiTest123!")

        assert login_page.wait_message("请输入正确的账号密码!") == "请输入正确的账号密码!"
        assert login_page.is_login_form_visible()

    def test_login_empty_password_validation(self, login_page):
        login_page.login("uitest", "")

        assert "请输入密码" in login_page.get_login_validation_messages()
        assert login_page.is_login_form_visible()

    def test_login_short_password_validation(self, login_page):
        login_page.login("uitest", "1234567")

        assert "密码长度请在八位以上" in login_page.get_login_validation_messages()
        assert login_page.is_login_form_visible()

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Known SUT defect: login username input is bound to FormItem prop='phone' "
            "while rules are defined for 'username', so empty username bypasses client validation."
        ),
    )
    def test_login_empty_username_known_validation_defect(self, login_page):
        login_page.login("", "UiTest123!")

        assert "请输入您的真实姓名" in login_page.get_login_validation_messages()

    def test_switch_to_register(self, login_page):
        login_page.switch_to_register()
        assert login_page.is_register_form_visible()

    def test_switch_to_login(self, login_page):
        login_page.switch_to_register().switch_to_login()
        assert login_page.is_login_form_visible()
