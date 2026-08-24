from __future__ import annotations

import pytest

from tools import get_logger, read_json_data
from utils.test_data_factory import RegistrationData, build_registration_data

logger = get_logger()


def _known_username() -> str | None:
    try:
        cases = read_json_data("login_data.json")
    except FileNotFoundError:
        return None
    for case in cases:
        if case.get("expected") == "success" and case.get("username"):
            return case["username"]
    return None


def _open_register(login_page):
    return login_page.switch_to_register()


def _submit(login_page, data: RegistrationData):
    return login_page.register(
        username=data.username,
        mail=data.mail,
        phone=data.phone,
        real_name=data.real_name,
        password=data.password,
    )


@pytest.mark.ui
class TestRegister:
    """注册模块：表单规则、用户名冲突、动态用户成功路径与已知 SUT 缺陷。"""

    def test_register_required_fields_validation(self, login_page):
        page = _open_register(login_page)
        page.submit_register()

        messages = page.get_register_validation_messages()
        assert "请输入您的真实姓名" in messages
        assert "请输入邮箱" in messages
        assert "请输入手机号" in messages
        assert "请输入密码" in messages

    def test_register_invalid_email_validation(self, login_page):
        data = build_registration_data()
        page = _open_register(login_page)
        page.register(
            username=data.username,
            mail="invalid-mail",
            phone=data.phone,
            real_name=data.real_name,
            password=data.password,
        )

        assert "请输入正确的邮箱号" in page.get_register_validation_messages()

    def test_register_invalid_phone_validation(self, login_page):
        data = build_registration_data()
        page = _open_register(login_page)
        page.register(
            username=data.username,
            mail=data.mail,
            phone="12345678901",
            real_name=data.real_name,
            password=data.password,
        )

        assert "请输入正确的手机号" in page.get_register_validation_messages()

    def test_register_short_password_validation(self, login_page):
        data = build_registration_data()
        page = _open_register(login_page)
        page.register(
            username=data.username,
            mail=data.mail,
            phone=data.phone,
            real_name=data.real_name,
            password="1234567",
        )

        assert "密码长度请在八位以上" in page.get_register_validation_messages()

    def test_register_existing_username(self, login_page):
        username = _known_username()
        if username is None:
            pytest.skip("本地 login_data.json 中没有可用于用户名冲突验证的真实账号")

        data = build_registration_data(username=username)
        page = _open_register(login_page)
        _submit(page, data)

        duplicate_messages = ("用户名已存在", "用户记录已存在")
        message = page.wait_message_any(duplicate_messages)

        assert any(expected in message for expected in duplicate_messages)
        assert page.is_register_form_visible()

    @pytest.mark.persistent_data
    def test_register_success_with_unique_user(self, login_page, home_page):
        data = build_registration_data()
        page = _open_register(login_page)
        _submit(page, data)

        home_page.wait_until_loaded()
        assert home_page.get_user_name() == home_page.expected_display_name(data.username)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "Known SUT defect: registration field prop='realName' but validation rules use "
            "'realNamee', so blank real name is not blocked by the intended client rule."
        ),
    )
    def test_register_empty_real_name_known_validation_defect(self, login_page):
        # Reuse an existing username so the request cannot create another user when the
        # broken client-side real-name rule lets submission continue.
        username = _known_username()
        if username is None:
            pytest.skip("本地 login_data.json 中没有可用于已知姓名校验缺陷复现的真实账号")

        data = build_registration_data(username=username)
        page = _open_register(login_page)
        page.register(
            username=data.username,
            mail=data.mail,
            phone=data.phone,
            real_name="",
            password=data.password,
        )

        assert "请输姓名" in page.get_register_validation_messages()
