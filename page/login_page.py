from __future__ import annotations

from collections.abc import Sequence

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from base.base_page import BasePage
from config import LOGIN_URL


class LoginPage(BasePage):
    """登录/注册入口页面对象。测试层只调用业务动作，不接触 Locator。"""

    # 登录和注册表单同时存在于 DOM 中，仅通过 hidden class 切换显示状态。
    _LOGIN_FORM = (By.CSS_SELECTOR, ".logon:not(.hidden)")
    _REGISTER_FORM = (By.CSS_SELECTOR, ".register:not(.hidden)")

    _USERNAME_INPUT = (
        By.CSS_SELECTOR,
        ".logon:not(.hidden) input[placeholder='请输入用户名']",
    )
    _PASSWORD_INPUT = (
        By.CSS_SELECTOR,
        ".logon:not(.hidden) input[placeholder='请输入密码']",
    )
    _LOGIN_BUTTON = (
        By.XPATH,
        "//div[contains(concat(' ', normalize-space(@class), ' '), ' logon ') "
        "and not(contains(concat(' ', normalize-space(@class), ' '), ' hidden '))]"
        "//button[.//span[normalize-space()='登录']]",
    )
    _REMEMBER_INPUT = (
        By.CSS_SELECTOR,
        ".logon:not(.hidden) label.el-checkbox input[type='checkbox']",
    )
    _REMEMBER_LABEL = (By.CSS_SELECTOR, ".logon:not(.hidden) label.el-checkbox")
    _LOGIN_VALIDATION_ERRORS = (
        By.CSS_SELECTOR,
        ".logon:not(.hidden) .el-form-item__error",
    )

    _REGISTER_USERNAME_INPUT = (
        By.CSS_SELECTOR,
        ".register:not(.hidden) input[placeholder='请输入用户名']",
    )
    _REGISTER_MAIL_INPUT = (
        By.CSS_SELECTOR,
        ".register:not(.hidden) input[placeholder='请输入邮箱']",
    )
    _REGISTER_PHONE_INPUT = (
        By.CSS_SELECTOR,
        ".register:not(.hidden) input[placeholder='请输入手机号']",
    )
    _REGISTER_REAL_NAME_INPUT = (
        By.CSS_SELECTOR,
        ".register:not(.hidden) input[placeholder='请输入姓名']",
    )
    _REGISTER_PASSWORD_INPUT = (
        By.CSS_SELECTOR,
        ".register:not(.hidden) input[placeholder='请输入密码']",
    )
    _REGISTER_BUTTON = (
        By.XPATH,
        "//div[contains(concat(' ', normalize-space(@class), ' '), ' register ') "
        "and not(contains(concat(' ', normalize-space(@class), ' '), ' hidden '))]"
        "//button[.//span[normalize-space()='注册']]",
    )
    _REGISTER_VALIDATION_ERRORS = (
        By.CSS_SELECTOR,
        ".register:not(.hidden) .el-form-item__error",
    )

    _REGISTER_SWITCH = (
        By.XPATH,
        "//div[contains(concat(' ', normalize-space(@class), ' '), ' move ')]"
        "//button[.//span[normalize-space()='去注册']]",
    )
    _LOGIN_SWITCH = (
        By.XPATH,
        "//div[contains(concat(' ', normalize-space(@class), ' '), ' move ')]"
        "//button[.//span[normalize-space()='去登录']]",
    )
    _MESSAGE = (By.CSS_SELECTOR, ".el-message .el-message__content")

    def open(self):
        self.open_url(LOGIN_URL)
        self.wait_until_loaded()
        return self

    def wait_until_loaded(self):
        self.wait_url_contains("/login")
        self.wait_login_form()
        return self

    def wait_login_form(self):
        self.wait_element_visible(self._LOGIN_FORM)
        self.wait_element_visible(self._LOGIN_BUTTON)
        return self

    def wait_register_form(self):
        self.wait_element_visible(self._REGISTER_FORM)
        self.wait_element_visible(self._REGISTER_BUTTON)
        self.wait_element_visible(self._LOGIN_SWITCH)
        return self

    def login(self, username: str, password: str, remember: bool = False):
        self.input_text(self._USERNAME_INPUT, username)
        self.input_text(self._PASSWORD_INPUT, password)
        if remember and not self.is_selected(self._REMEMBER_INPUT):
            self.click(self._REMEMBER_LABEL)
        return self.submit_login()

    def submit_login(self):
        self.click(self._LOGIN_BUTTON)
        return self

    def register(
        self,
        *,
        username: str,
        mail: str,
        phone: str,
        real_name: str,
        password: str,
    ):
        self.input_text(self._REGISTER_USERNAME_INPUT, username)
        self.input_text(self._REGISTER_MAIL_INPUT, mail)
        self.input_text(self._REGISTER_PHONE_INPUT, phone)
        self.input_text(self._REGISTER_REAL_NAME_INPUT, real_name)
        self.input_text(self._REGISTER_PASSWORD_INPUT, password)
        return self.submit_register()

    def submit_register(self):
        self.click(self._REGISTER_BUTTON)
        return self

    def switch_to_register(self):
        self.click(self._REGISTER_SWITCH)
        self.wait_register_form()
        return self

    def switch_to_login(self):
        self.click(self._LOGIN_SWITCH)
        self.wait_login_form()
        return self

    def is_login_form_visible(self, timeout: int = 3) -> bool:
        return self.is_visible(self._LOGIN_FORM, timeout=timeout)

    def is_register_form_visible(self, timeout: int = 3) -> bool:
        return self.is_visible(self._REGISTER_FORM, timeout=timeout)

    def get_login_validation_messages(self, timeout: int = 3) -> list[str]:
        return [
            element.text.strip()
            for element in self.wait_elements_visible(self._LOGIN_VALIDATION_ERRORS, timeout)
            if element.text.strip()
        ]

    def get_register_validation_messages(self, timeout: int = 3) -> list[str]:
        return [
            element.text.strip()
            for element in self.wait_elements_visible(self._REGISTER_VALIDATION_ERRORS, timeout)
            if element.text.strip()
        ]

    def wait_message_contains(self, text: str, timeout: int = 5) -> str:
        """Wait for a user-visible message containing stable business text."""
        return self.wait_text_visible(self._MESSAGE, text, timeout=timeout).text.strip()

    def wait_message_any(self, texts: Sequence[str], timeout: int = 5) -> str:
        """Wait until any allowed business message is visible and return its full text."""
        expected = tuple(text for text in texts if text)
        if not expected:
            raise ValueError("texts must contain at least one non-empty message")

        def _matching_message(driver):
            for element in driver.find_elements(*self._MESSAGE):
                if not element.is_displayed():
                    continue
                message = element.text.strip()
                if any(text in message for text in expected):
                    return message
            return False

        return WebDriverWait(self.driver, self._timeout(timeout)).until(_matching_message)

    def wait_message(self, text: str, timeout: int = 5) -> str:
        """Backward-compatible alias for existing authentication cases."""
        return self.wait_message_contains(text, timeout=timeout)

    def get_error_msg(self, timeout: int = 3) -> str:
        """兼容旧调用；新用例优先使用 wait_message 明确等待业务反馈。"""
        return (
            self.get_text(self._MESSAGE, timeout=timeout)
            if self.is_visible(self._MESSAGE, timeout=timeout)
            else ""
        )
