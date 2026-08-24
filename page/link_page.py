from __future__ import annotations

from typing import NamedTuple

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait

from base.base_page import BasePage
from tools import get_logger


logger = get_logger()


class LinkRecord(NamedTuple):
    description: str
    origin_url: str
    short_url: str


class LinkPage(BasePage):
    """My Space short-link list and create/edit lifecycle page object."""

    # The frontend table derives its generated URL from row.fullShortUrl.
    _CREATE_BUTTON = (By.XPATH, "//button[.//span[normalize-space()='创建短链']]")
    _DIALOGS = (By.CSS_SELECTOR, ".el-dialog")
    _DIALOG_TITLE = ".el-dialog__title"
    _TABLE_ROWS = (By.CSS_SELECTOR, ".el-table__body tbody tr")
    _ROW_INFO = ".table-link-box"
    _ROW_DESCRIPTION = ".table-link-box span"
    _ROW_SHORT_LINK = "a.el-link[href]"
    _ROW_ORIGIN_URL = ".table-url-box > span"
    _SELECTED_GROUP_NAME = ".sortOptions .item-box.selectedItem .over-text"
    _RECYCLE_BIN_TRIGGER = (By.CSS_SELECTOR, ".recycle-box")
    _RECYCLE_BIN_SELECTED = (By.CSS_SELECTOR, ".recycle-box.selectedItem")
    _RECYCLE_HEADER = (By.CSS_SELECTOR, ".recycle-bin-box")
    _ROW_ACTION_BUTTONS = "td:last-child .table-edit"
    _FORM_ERROR = ".el-form-item__error"
    _MESSAGE = (By.CSS_SELECTOR, ".el-message .el-message__content")
    _POPPERS = (By.CSS_SELECTOR, ".el-popper")

    _CREATE_ORIGIN_PLACEHOLDER = "请输入http://或https://开头的链接或应用跳转链接"
    _CREATE_DESCRIPTION_PLACEHOLDER = "请输入描述信息"
    _EDIT_DESCRIPTION_PLACEHOLDER = "可通过换行创建多个短链，一行一个，单次最多创建50条"

    CREATE_DIALOG_TITLE = "创建链接"
    EDIT_DIALOG_TITLE = "编辑链接"

    def wait_until_loaded(self):
        self.wait_url_contains("/home/space")
        self.wait_element_visible(self._CREATE_BUTTON)
        return self

    def _visible_dialog(self, title: str, timeout: int | None = None) -> WebElement:
        def _matching_dialog(driver):
            for dialog in driver.find_elements(*self._DIALOGS):
                try:
                    if not dialog.is_displayed():
                        continue
                    titles = dialog.find_elements(By.CSS_SELECTOR, self._DIALOG_TITLE)
                    if titles and titles[0].text.strip() == title:
                        return dialog
                except StaleElementReferenceException:
                    continue
            return False

        return WebDriverWait(self.driver, self._timeout(timeout)).until(_matching_dialog)

    def _wait_dialog_hidden(self, title: str, timeout: int | None = None) -> bool:
        def _hidden(driver):
            for dialog in driver.find_elements(*self._DIALOGS):
                try:
                    if not dialog.is_displayed():
                        continue
                    titles = dialog.find_elements(By.CSS_SELECTOR, self._DIALOG_TITLE)
                    if titles and titles[0].text.strip() == title:
                        return False
                except StaleElementReferenceException:
                    continue
            return True

        return WebDriverWait(self.driver, self._timeout(timeout)).until(_hidden)

    @staticmethod
    def _dialog_button(dialog: WebElement, text: str) -> WebElement:
        for button in dialog.find_elements(By.CSS_SELECTOR, "button"):
            if button.is_displayed() and button.text.strip() == text:
                return button
        raise LookupError(f"弹窗中未找到按钮: {text}")

    def _replace_element_value(self, element: WebElement, text: str) -> None:
        element.send_keys(Keys.CONTROL, "a")
        element.send_keys(Keys.BACKSPACE)
        WebDriverWait(self.driver, self.timeout).until(
            lambda _: (element.get_attribute("value") or "") == ""
        )
        if text:
            element.send_keys(text)
        else:
            element.send_keys(Keys.TAB)

    def _fill_create_dialog_with_explicit_description(
        self,
        dialog: WebElement,
        *,
        origin_url: str,
        description: str,
    ) -> None:
        # CreateLink.vue auto-fetches the page title when originUrl changes while
        # describe is empty. Prime the explicit test description first so that
        # normal CRUD cases do not race with the external title request.
        area = dialog.find_element(
            By.CSS_SELECTOR,
            f"textarea[placeholder='{self._CREATE_DESCRIPTION_PLACEHOLDER}']",
        )
        self._replace_element_value(area, description)
        origin = dialog.find_element(
            By.CSS_SELECTOR,
            f"input[placeholder='{self._CREATE_ORIGIN_PLACEHOLDER}']",
        )
        self._replace_element_value(origin, origin_url)

    def _fill_link_dialog(
        self,
        dialog: WebElement,
        *,
        origin_url: str | None = None,
        description: str | None = None,
        editing: bool = False,
    ) -> None:
        if not editing and origin_url is not None and description is not None:
            self._fill_create_dialog_with_explicit_description(
                dialog,
                origin_url=origin_url,
                description=description,
            )
            return

        if origin_url is not None:
            origin = dialog.find_element(
                By.CSS_SELECTOR,
                f"input[placeholder='{self._CREATE_ORIGIN_PLACEHOLDER}']",
            )
            self._replace_element_value(origin, origin_url)
        if description is not None:
            placeholder = (
                self._EDIT_DESCRIPTION_PLACEHOLDER if editing else self._CREATE_DESCRIPTION_PLACEHOLDER
            )
            area = dialog.find_element(By.CSS_SELECTOR, f"textarea[placeholder='{placeholder}']")
            self._replace_element_value(area, description)

    def _visible_rows(self) -> list[WebElement]:
        rows = self.driver.find_elements(*self._TABLE_ROWS)
        visible: list[WebElement] = []
        for row in rows:
            try:
                if row.is_displayed():
                    visible.append(row)
            except StaleElementReferenceException:
                continue
        return visible

    @staticmethod
    def _row_description(row: WebElement) -> str:
        for element in row.find_elements(By.CSS_SELECTOR, ".table-link-box span"):
            if element.is_displayed():
                text = element.text.strip()
                if text:
                    return text
        return ""

    def _find_row(self, description: str, timeout: int | None = None) -> WebElement:
        def _matching_row(_):
            for row in self._visible_rows():
                try:
                    if self._row_description(row) == description:
                        return row
                except StaleElementReferenceException:
                    continue
            return False

        return WebDriverWait(self.driver, self._timeout(timeout)).until(_matching_row)


    def _row_action_button(self, row: WebElement, index: int) -> WebElement:
        buttons = [
            button
            for button in row.find_elements(By.CSS_SELECTOR, self._ROW_ACTION_BUTTONS)
            if button.is_displayed()
        ]
        if len(buttons) <= index:
            raise LookupError(f"短链操作按钮数量不足: expected index={index}, actual={len(buttons)}")
        return buttons[index]

    def _confirm_popover(self, title_fragment: str, timeout: int | None = None) -> None:
        def _confirmation_button(driver):
            for popper in driver.find_elements(*self._POPPERS):
                try:
                    if not popper.is_displayed() or title_fragment not in popper.text:
                        continue
                    buttons = [
                        button
                        for button in popper.find_elements(By.CSS_SELECTOR, "button")
                        if button.is_displayed() and button.is_enabled()
                    ]
                    for button in buttons:
                        classes = button.get_attribute("class") or ""
                        if "el-button--primary" in classes:
                            return button
                    if buttons:
                        return buttons[-1]
                except StaleElementReferenceException:
                    continue
            return False

        WebDriverWait(self.driver, self._timeout(timeout)).until(_confirmation_button).click()

    def _confirm_recycle_popover(self, timeout: int | None = None) -> None:
        self._confirm_popover("是否移入回收站", timeout=timeout)

    def open_create_dialog(self):
        self.click(self._CREATE_BUTTON)
        self._visible_dialog(self.CREATE_DIALOG_TITLE)
        return self

    def submit_create_form(self, origin_url: str, description: str):
        self.open_create_dialog()
        dialog = self._visible_dialog(self.CREATE_DIALOG_TITLE)
        self._fill_link_dialog(dialog, origin_url=origin_url, description=description)
        self._dialog_button(dialog, "确认").click()
        return self

    def close_create_dialog(self):
        dialog = self._visible_dialog(self.CREATE_DIALOG_TITLE)
        self._dialog_button(dialog, "取消").click()
        self._wait_dialog_hidden(self.CREATE_DIALOG_TITLE)
        return self

    def get_create_description_value(self) -> str:
        dialog = self._visible_dialog(self.CREATE_DIALOG_TITLE)
        area = dialog.find_element(
            By.CSS_SELECTOR,
            f"textarea[placeholder='{self._CREATE_DESCRIPTION_PLACEHOLDER}']",
        )
        return (area.get_attribute("value") or "").strip()

    def enter_origin_and_wait_description(self, origin_url: str, timeout: int | None = None) -> str:
        """Trigger the real CreateLink title lookup and return the auto-filled description."""
        dialog = self._visible_dialog(self.CREATE_DIALOG_TITLE)
        origin = dialog.find_element(
            By.CSS_SELECTOR,
            f"input[placeholder='{self._CREATE_ORIGIN_PLACEHOLDER}']",
        )
        self._replace_element_value(origin, origin_url)

        def _autofilled(_):
            value = self.get_create_description_value()
            if value == "Error while fetching title.":
                raise AssertionError("目标网站标题抓取失败: " + origin_url)
            return value or False

        return WebDriverWait(self.driver, self._timeout(timeout)).until(_autofilled)

    def create_link(self, origin_url: str, description: str):
        self.submit_create_form(origin_url, description)
        self._wait_dialog_hidden(self.CREATE_DIALOG_TITLE)
        self.wait_link_created(description, origin_url)
        return self

    def cancel_create_link(self, origin_url: str, description: str):
        before = self.get_link_count()
        self.open_create_dialog()
        dialog = self._visible_dialog(self.CREATE_DIALOG_TITLE)
        self._fill_link_dialog(dialog, origin_url=origin_url, description=description)
        self._dialog_button(dialog, "取消").click()
        self._wait_dialog_hidden(self.CREATE_DIALOG_TITLE)
        WebDriverWait(self.driver, self.timeout).until(lambda _: self.get_link_count() == before)
        return self

    def get_create_validation_messages(self, timeout: int = 5) -> list[str]:
        dialog = self._visible_dialog(self.CREATE_DIALOG_TITLE)

        def _messages(_):
            messages = [
                element.text.strip()
                for element in dialog.find_elements(By.CSS_SELECTOR, self._FORM_ERROR)
                if element.is_displayed() and element.text.strip()
            ]
            return messages or False

        return WebDriverWait(self.driver, self._timeout(timeout)).until(_messages)

    def get_link_count(self) -> int:
        return len(self._visible_rows())

    def has_link(self, description: str, timeout: int = 3) -> bool:
        try:
            self._find_row(description, timeout=timeout)
            return True
        except TimeoutException:
            return False

    def wait_link_present(self, description: str, timeout: int | None = None):
        self._find_row(description, timeout=timeout)
        return self

    def _link_creation_diagnostics(self, description: str) -> dict[str, object]:
        descriptions: list[str] = []
        matched_record: LinkRecord | None = None
        for row in self._visible_rows():
            try:
                row_description = self._row_description(row)
                descriptions.append(row_description)
                if row_description == description:
                    matched_record = self._record_from_row(row)
            except StaleElementReferenceException:
                continue

        selected_group = ""
        for element in self.driver.find_elements(By.CSS_SELECTOR, self._SELECTED_GROUP_NAME):
            try:
                if element.is_displayed():
                    selected_group = element.text.strip()
                    break
            except StaleElementReferenceException:
                continue

        return {
            "descriptions": descriptions,
            "matched_row": matched_record is not None,
            "actual_origin_url": matched_record.origin_url if matched_record else "",
            "actual_short_url": matched_record.short_url if matched_record else "",
            "selected_group": selected_group,
        }

    def wait_link_created(
        self,
        description: str,
        origin_url: str,
        timeout: int | None = None,
    ) -> LinkRecord:
        """Wait until the created row exposes the expected business state."""

        def _created(_):
            record = self._link_record_if_present(description)
            if record is None or not record.short_url:
                return False
            if record.origin_url.rstrip("/") != origin_url.rstrip("/"):
                return False
            return record

        try:
            return WebDriverWait(self.driver, self._timeout(timeout)).until(_created)
        except TimeoutException as exc:
            diagnostics = self._link_creation_diagnostics(description)
            message = (
                "短链创建后置条件超时: "
                f"expected_description={description!r}, "
                f"expected_origin_url={origin_url!r}, "
                f"diagnostics={diagnostics!r}"
            )
            logger.error(message)
            raise TimeoutException(message) from exc

    def wait_link_absent(self, description: str, timeout: int | None = None):
        def _absent(_):
            try:
                return all(self._row_description(row) != description for row in self._visible_rows())
            except StaleElementReferenceException:
                return False

        WebDriverWait(self.driver, self._timeout(timeout)).until(_absent)
        return self

    def _record_from_row(self, row: WebElement) -> LinkRecord:
        anchor = row.find_element(By.CSS_SELECTOR, self._ROW_SHORT_LINK)
        origin = row.find_element(By.CSS_SELECTOR, self._ROW_ORIGIN_URL)
        return LinkRecord(
            description=self._row_description(row),
            origin_url=origin.text.strip(),
            short_url=anchor.get_attribute("href") or "",
        )

    def _link_record_if_present(self, description: str) -> LinkRecord | None:
        for row in self._visible_rows():
            try:
                if self._row_description(row) == description:
                    return self._record_from_row(row)
            except StaleElementReferenceException:
                continue
        return None

    def get_link_record(self, description: str) -> LinkRecord:
        row = self._find_row(description)
        return self._record_from_row(row)

    def edit_link(
        self,
        description: str,
        *,
        origin_url: str | None = None,
        new_description: str | None = None,
    ):
        row = self._find_row(description)
        # Frontend operation order is chart, edit, delete.
        self._row_action_button(row, 1).click()
        dialog = self._visible_dialog(self.EDIT_DIALOG_TITLE)
        self._fill_link_dialog(
            dialog,
            origin_url=origin_url,
            description=new_description,
            editing=True,
        )
        self._dialog_button(dialog, "确认").click()
        self._wait_dialog_hidden(self.EDIT_DIALOG_TITLE)
        expected_description = new_description or description

        def _updated(_):
            try:
                record = self.get_link_record(expected_description)
            except (TimeoutException, StaleElementReferenceException):
                return False
            if origin_url is not None and record.origin_url != origin_url:
                return False
            return record

        WebDriverWait(self.driver, self.timeout).until(_updated)
        return self

    def open_short_link_and_get_final_url(self, description: str) -> str:
        row = self._find_row(description)
        anchor = row.find_element(By.CSS_SELECTOR, self._ROW_SHORT_LINK)
        original_handle = self.driver.current_window_handle
        before = set(self.driver.window_handles)
        anchor.click()

        new_handle = WebDriverWait(self.driver, self.timeout).until(
            lambda d: next((handle for handle in d.window_handles if handle not in before), False)
        )
        self.driver.switch_to.window(new_handle)
        try:
            return WebDriverWait(self.driver, self.timeout).until(
                lambda d: d.current_url if d.current_url and d.current_url != "about:blank" else False
            )
        finally:
            self.driver.close()
            self.driver.switch_to.window(original_handle)


    def move_link_to_recycle(self, description: str):
        row = self._find_row(description)
        # Frontend operation order is chart, edit, delete/recycle.
        self._row_action_button(row, 2).click()
        self._confirm_recycle_popover()
        self.wait_link_absent(description)
        return self

    def open_recycle_bin(self):
        self.click(self._RECYCLE_BIN_TRIGGER)
        self.wait_element_visible(self._RECYCLE_HEADER)
        self.wait_element_visible(self._RECYCLE_BIN_SELECTED)
        return self

    def open_url_and_get_final_url(self, url: str) -> str:
        original_handle = self.driver.current_window_handle
        self.driver.switch_to.new_window("tab")
        try:
            self.driver.get(url)
            return WebDriverWait(self.driver, self.timeout).until(
                lambda d: d.current_url if d.current_url and d.current_url != "about:blank" else False
            )
        finally:
            self.driver.close()
            self.driver.switch_to.window(original_handle)

    def recover_link(self, description: str):
        row = self._find_row(description)
        # Recycle mode operation order is chart, recover, permanent delete.
        self._row_action_button(row, 1).click()
        self.wait_link_absent(description)
        return self

    def permanently_delete_link(self, description: str):
        row = self._find_row(description)
        # Recycle mode operation order is chart, recover, permanent delete.
        self._row_action_button(row, 2).click()
        self._confirm_popover("不可逆")
        self.wait_link_absent(description)
        return self
