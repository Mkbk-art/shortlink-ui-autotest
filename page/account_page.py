from __future__ import annotations

from typing import NamedTuple

from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from base.base_page import BasePage


class AccountProfile(NamedTuple):
    username: str
    phone: str
    real_name: str
    mail: str


class AccountPage(BasePage):
    """Account profile page and reversible profile editing behavior."""

    _PROFILE_TITLE = (By.CSS_SELECTOR, ".el-descriptions__title")
    _USERNAME_VALUE = (
        By.XPATH,
        "//td[contains(@class,'el-descriptions__label') and contains(normalize-space(.),'用户名')]"
        "/following-sibling::td[contains(@class,'el-descriptions__content')][1]",
    )
    _PHONE_VALUE = (
        By.XPATH,
        "//td[contains(@class,'el-descriptions__label') and contains(normalize-space(.),'手机号')]"
        "/following-sibling::td[contains(@class,'el-descriptions__content')][1]",
    )
    _REAL_NAME_VALUE = (
        By.XPATH,
        "//td[contains(@class,'el-descriptions__label') and contains(normalize-space(.),'姓名')]"
        "/following-sibling::td[contains(@class,'el-descriptions__content')][1]",
    )
    _MAIL_VALUE = (
        By.XPATH,
        "//td[contains(@class,'el-descriptions__label') and contains(normalize-space(.),'邮箱')]"
        "/following-sibling::td[contains(@class,'el-descriptions__content')][1]",
    )
    _EDIT_BUTTON = (By.XPATH, "//button[.//span[normalize-space()='修改个人信息']]")
    _DIALOGS = (By.CSS_SELECTOR, ".el-dialog")
    _DIALOG_TITLE = ".el-dialog__title"
    _MAIL_INPUT = "input[placeholder='请输入邮箱']"
    _FORM_ERROR = ".el-form-item__error"

    def wait_until_loaded(self):
        self.wait_url_contains("/home/account")
        self.wait_text_visible(self._PROFILE_TITLE, "个人信息")
        return self

    def get_profile(self) -> AccountProfile:
        return AccountProfile(
            username=self.get_text(self._USERNAME_VALUE).strip(),
            phone=self.get_text(self._PHONE_VALUE).strip(),
            real_name=self.get_text(self._REAL_NAME_VALUE).strip(),
            mail=self.get_text(self._MAIL_VALUE).strip(),
        )

    def _visible_edit_dialog(self, timeout: int | None = None) -> WebElement:
        def _dialog(driver):
            for dialog in driver.find_elements(*self._DIALOGS):
                try:
                    if not dialog.is_displayed():
                        continue
                    title = dialog.find_element(By.CSS_SELECTOR, self._DIALOG_TITLE).text.strip()
                    if title == "修改个人信息":
                        return dialog
                except StaleElementReferenceException:
                    continue
            return False

        return WebDriverWait(self.driver, self._timeout(timeout)).until(_dialog)

    @staticmethod
    def _dialog_button(dialog: WebElement, text: str) -> WebElement:
        for button in dialog.find_elements(By.CSS_SELECTOR, "button"):
            if button.is_displayed() and button.text.strip() == text:
                return button
        raise LookupError(f"修改个人信息弹窗中未找到按钮: {text}")

    @staticmethod
    def _replace_value(element: WebElement, value: str) -> None:
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.BACKSPACE)
        element.send_keys(value)
        element.send_keys(Keys.TAB)


    def close_edit_dialog_if_open(self) -> bool:
        for dialog in self.driver.find_elements(*self._DIALOGS):
            try:
                if not dialog.is_displayed():
                    continue
                title = dialog.find_element(By.CSS_SELECTOR, self._DIALOG_TITLE).text.strip()
                if title != "修改个人信息":
                    continue
                self._dialog_button(dialog, "取消").click()
                WebDriverWait(self.driver, self.timeout).until(lambda _: not dialog.is_displayed())
                return True
            except StaleElementReferenceException:
                continue
        return False

    def update_mail(self, mail: str):
        self.click(self._EDIT_BUTTON)
        dialog = self._visible_edit_dialog()
        mail_input = dialog.find_element(By.CSS_SELECTOR, self._MAIL_INPUT)
        self._replace_value(mail_input, mail)
        self._dialog_button(dialog, "提交").click()

        def _outcome(_):
            try:
                if not dialog.is_displayed():
                    return "updated"
            except StaleElementReferenceException:
                return "updated"

            errors = [
                element.text.strip()
                for element in dialog.find_elements(By.CSS_SELECTOR, self._FORM_ERROR)
                if element.is_displayed() and element.text.strip()
            ]
            return ("rejected", errors) if errors else False

        outcome = WebDriverWait(self.driver, self.timeout).until(_outcome)
        if isinstance(outcome, tuple) and outcome[0] == "rejected":
            raise AssertionError(f"个人信息修改被前端校验拒绝: {outcome[1]}")

        WebDriverWait(self.driver, self.timeout).until(lambda _: self.get_profile().mail == mail)
        return self
