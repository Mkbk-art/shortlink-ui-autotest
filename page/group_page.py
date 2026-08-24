from __future__ import annotations

from collections.abc import Sequence

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from base.base_page import BasePage


class GroupPage(BasePage):
    """“我的空间”短链分组页面对象。所有分组 DOM 细节只保留在这里。"""

    _GROUP_AREA = (By.CSS_SELECTOR, ".options-box")
    _SORT_LIST = (By.CSS_SELECTOR, ".sortOptions")
    _GROUP_ROWS = (By.CSS_SELECTOR, ".sortOptions > li")
    _GROUP_ITEM = ".item-box"
    _GROUP_NAME = ".over-text"
    _SELECTED_ITEM = ".item-box.selectedItem"
    _GROUP_TOOL = ".block .edit"
    _CREATE_TRIGGER = (By.CSS_SELECTOR, ".option-title .hover-box")
    _DIALOGS = (By.CSS_SELECTOR, ".el-dialog")
    _DIALOG_TITLE = ".el-dialog__title"
    _DIALOG_INPUT = "input.el-input__inner"
    _DIALOG_BUTTONS = ".el-dialog__footer button"
    _DROPDOWN_ITEMS = (By.CSS_SELECTOR, ".el-dropdown-menu__item")
    _MESSAGE = (By.CSS_SELECTOR, ".el-message .el-message__content")

    CREATE_DIALOG_TITLE = "新建短链接分组"
    EDIT_DIALOG_TITLE = "编辑短链接分组"

    def wait_until_loaded(self):
        self.wait_url_contains("/home/space")
        self.wait_element_visible(self._GROUP_AREA)
        self.wait_element_visible(self._SORT_LIST)
        return self

    def _visible_rows(self) -> list[WebElement]:
        rows = self.driver.find_elements(*self._GROUP_ROWS)
        return [row for row in rows if row.is_displayed()]

    @staticmethod
    def _row_name(row: WebElement) -> str:
        return row.find_element(By.CSS_SELECTOR, ".over-text").text.strip()

    def _find_row(self, group_name: str, timeout: int | None = None) -> WebElement:
        def _matching_row(_):
            for row in self._visible_rows():
                if self._row_name(row) == group_name:
                    return row
            return False

        return WebDriverWait(self.driver, self._timeout(timeout)).until(_matching_row)

    def _visible_dialog(self, title: str, timeout: int | None = None) -> WebElement:
        def _matching_dialog(driver):
            for dialog in driver.find_elements(*self._DIALOGS):
                if not dialog.is_displayed():
                    continue
                titles = dialog.find_elements(By.CSS_SELECTOR, self._DIALOG_TITLE)
                if titles and titles[0].text.strip() == title:
                    return dialog
            return False

        return WebDriverWait(self.driver, self._timeout(timeout)).until(_matching_dialog)

    @staticmethod
    def _dialog_button(dialog: WebElement, text: str) -> WebElement:
        for button in dialog.find_elements(By.CSS_SELECTOR, ".el-dialog__footer button"):
            if button.is_displayed() and text in button.text.strip():
                return button
        raise LookupError(f"弹窗中未找到按钮: {text}")

    def _replace_dialog_input(self, dialog: WebElement, text: str) -> None:
        input_element = dialog.find_element(By.CSS_SELECTOR, self._DIALOG_INPUT)
        input_element.send_keys(Keys.CONTROL, "a")
        if text:
            input_element.send_keys(text)
            WebDriverWait(self.driver, self.timeout).until(
                lambda _: dialog.find_element(By.CSS_SELECTOR, self._DIALOG_INPUT).get_attribute("value") == text
            )
        else:
            input_element.send_keys(Keys.BACKSPACE)
            WebDriverWait(self.driver, self.timeout).until(
                lambda _: dialog.find_element(By.CSS_SELECTOR, self._DIALOG_INPUT).get_attribute("value") == ""
            )

    def _wait_message_any(self, texts: Sequence[str], timeout: int = 5) -> str:
        expected = tuple(text for text in texts if text)

        def _message(driver):
            for element in driver.find_elements(*self._MESSAGE):
                if not element.is_displayed():
                    continue
                message = element.text.strip()
                if any(text in message for text in expected):
                    return message
            return False

        return WebDriverWait(self.driver, self._timeout(timeout)).until(_message)

    def _open_group_actions(self, group_name: str) -> None:
        row = self._find_row(group_name)
        ActionChains(self.driver).move_to_element(row).perform()
        tool = WebDriverWait(self.driver, self.timeout).until(
            lambda _: next(
                (
                    element
                    for element in row.find_elements(By.CSS_SELECTOR, self._GROUP_TOOL)
                    if element.is_displayed()
                ),
                False,
            )
        )
        # Element Plus el-dropdown uses hover by default; hover the actual trigger.
        ActionChains(self.driver).move_to_element(tool).perform()

    def _click_visible_dropdown_item(self, text: str) -> None:
        def _item(driver):
            for element in driver.find_elements(*self._DROPDOWN_ITEMS):
                if element.is_displayed() and element.text.strip() == text:
                    return element
            return False

        WebDriverWait(self.driver, self.timeout).until(_item).click()

    def get_group_names(self) -> list[str]:
        return [self._row_name(row) for row in self._visible_rows()]

    def group_count(self) -> int:
        return len(self._visible_rows())

    def blank_group_count(self) -> int:
        return sum(name == "" for name in self.get_group_names())

    def has_group(self, group_name: str, timeout: int = 3) -> bool:
        try:
            self._find_row(group_name, timeout=timeout)
            return True
        except TimeoutException:
            return False

    def wait_group_present(self, group_name: str, timeout: int | None = None):
        self._find_row(group_name, timeout=timeout)
        return self

    def wait_group_absent(self, group_name: str, timeout: int | None = None):
        def _group_absent(_):
            try:
                return all(name != group_name for name in self.get_group_names())
            except StaleElementReferenceException:
                # Vue refreshes the list after mutations; let the next poll query fresh DOM nodes.
                return False

        WebDriverWait(self.driver, self._timeout(timeout)).until(_group_absent)
        return self

    def open_create_dialog(self):
        self.click(self._CREATE_TRIGGER)
        self._visible_dialog(self.CREATE_DIALOG_TITLE)
        return self

    def create_group(self, group_name: str):
        self.open_create_dialog()
        dialog = self._visible_dialog(self.CREATE_DIALOG_TITLE)
        self._replace_dialog_input(dialog, group_name)
        self._dialog_button(dialog, "确认").click()
        self.wait_group_present(group_name)
        return self

    def cancel_create_group(self, group_name: str):
        self.open_create_dialog()
        dialog = self._visible_dialog(self.CREATE_DIALOG_TITLE)
        self._replace_dialog_input(dialog, group_name)
        self._dialog_button(dialog, "取消").click()
        WebDriverWait(self.driver, self.timeout).until(lambda _: not dialog.is_displayed())
        self.wait_group_absent(group_name, timeout=3)
        return self

    def rename_group(self, old_name: str, new_name: str):
        self._open_group_actions(old_name)
        self._click_visible_dropdown_item("编辑")
        dialog = self._visible_dialog(self.EDIT_DIALOG_TITLE)
        self._replace_dialog_input(dialog, new_name)
        self._dialog_button(dialog, "确认").click()
        self.wait_group_present(new_name)
        self.wait_group_absent(old_name)
        return self

    def delete_group(self, group_name: str):
        self._open_group_actions(group_name)
        self._click_visible_dropdown_item("删除")
        self.wait_group_absent(group_name)
        return self

    def select_group(self, group_name: str):
        row = self._find_row(group_name)
        row.find_element(By.CSS_SELECTOR, self._GROUP_ITEM).click()
        WebDriverWait(self.driver, self.timeout).until(
            lambda _: "selectedItem"
            in (self._find_row(group_name).find_element(By.CSS_SELECTOR, self._GROUP_ITEM).get_attribute("class") or "")
        )
        return self

    def is_group_selected(self, group_name: str, timeout: int = 3) -> bool:
        try:
            row = self._find_row(group_name, timeout=timeout)
        except TimeoutException:
            return False
        classes = row.find_element(By.CSS_SELECTOR, self._GROUP_ITEM).get_attribute("class") or ""
        return "selectedItem" in classes.split()

    def drag_group_onto(self, source_name: str, target_name: str) -> tuple[list[str], list[str]]:
        before = self.get_group_names()
        source = self._find_row(source_name)
        target = self._find_row(target_name)
        ActionChains(self.driver).click_and_hold(source).move_to_element(target).release().perform()

        def _changed(_):
            current = self.get_group_names()
            if current != before:
                return current
            return False

        after = WebDriverWait(self.driver, self.timeout).until(_changed)
        return before, after

    def create_blank_group(self):
        """Create one blank-name group and wait for the persistent list delta."""
        before = self.blank_group_count()
        self.open_create_dialog()
        dialog = self._visible_dialog(self.CREATE_DIALOG_TITLE)
        self._replace_dialog_input(dialog, "")
        self._dialog_button(dialog, "确认").click()

        def _created(_):
            try:
                return self.blank_group_count() == before + 1
            except StaleElementReferenceException:
                return False

        WebDriverWait(self.driver, self.timeout).until(_created)
        return self

    def delete_one_blank_group(self) -> bool:
        before = self.blank_group_count()
        if before == 0:
            return False

        self._open_group_actions("")
        self._click_visible_dropdown_item("删除")

        def _deleted(_):
            try:
                return self.blank_group_count() == before - 1
            except StaleElementReferenceException:
                return False

        WebDriverWait(self.driver, self.timeout).until(_deleted)
        return True
