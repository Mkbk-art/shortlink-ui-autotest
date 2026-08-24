from __future__ import annotations

from typing import List, Tuple

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from config import EXPLICITLY_WAIT
from tools import get_logger

logger = get_logger()
Locator = Tuple[str, str]


class BasePage:
    """Page-object base class exposing explicit, reusable browser operations."""

    def __init__(self, driver, timeout: int | None = None):
        self.driver = driver
        self.timeout = timeout if timeout is not None else EXPLICITLY_WAIT

    def _timeout(self, timeout: int | None) -> int:
        return self.timeout if timeout is None else timeout

    # ==================== 元素定位 ====================
    def find_element(self, locator: Locator, timeout: int | None = None) -> WebElement:
        return WebDriverWait(self.driver, self._timeout(timeout)).until(
            EC.presence_of_element_located(locator)
        )

    def find_elements(self, locator: Locator, timeout: int | None = None) -> List[WebElement]:
        return WebDriverWait(self.driver, self._timeout(timeout)).until(
            EC.presence_of_all_elements_located(locator)
        )

    # ==================== 元素操作 ====================
    def click(self, locator: Locator, timeout: int | None = None) -> None:
        element = WebDriverWait(self.driver, self._timeout(timeout)).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()
        logger.info("点击元素: %s", locator)

    def input_text(
        self,
        locator: Locator,
        text: str,
        clear_first: bool = True,
        timeout: int | None = None,
    ) -> None:
        element = self.wait_element_visible(locator, timeout)

        if clear_first:
            # Replace non-empty input in one keyboard flow and synchronize on the
            # durable final value. Waiting for the transient empty state before
            # typing creates a race with reactive Element Plus inputs.
            element.send_keys(Keys.CONTROL, "a")
            if text:
                element.send_keys(text)
                WebDriverWait(self.driver, self._timeout(timeout)).until(
                    lambda driver: driver.find_element(*locator).get_attribute("value") == text
                )
            else:
                element.send_keys(Keys.BACKSPACE)
                WebDriverWait(self.driver, self._timeout(timeout)).until(
                    lambda driver: driver.find_element(*locator).get_attribute("value") == ""
                )
                # Blur commits the empty value and triggers client-side validation.
                self.wait_element_visible(locator, timeout).send_keys(Keys.TAB)
        elif text:
            element.send_keys(text)
        else:
            element.send_keys(Keys.TAB)

        # Do not log typed values: password and other sensitive input may pass here.
        logger.info("输入元素: %s", locator)

    def get_text(self, locator: Locator, timeout: int | None = None) -> str:
        return self.wait_element_visible(locator, timeout).text

    def get_attribute(self, locator: Locator, attribute: str, timeout: int | None = None):
        return self.find_element(locator, timeout).get_attribute(attribute)

    # ==================== 元素状态 ====================
    def is_visible(self, locator: Locator, timeout: int = 3) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(EC.visibility_of_element_located(locator))
            return True
        except TimeoutException:
            return False

    def is_clickable(self, locator: Locator, timeout: int = 3) -> bool:
        try:
            WebDriverWait(self.driver, timeout).until(EC.element_to_be_clickable(locator))
            return True
        except TimeoutException:
            return False

    def is_selected(self, locator: Locator) -> bool:
        return self.find_element(locator).is_selected()

    # ==================== 浏览器操作 ====================
    def open_url(self, url: str) -> None:
        self.driver.get(url)
        logger.info("打开页面: %s", url)

    def get_url(self) -> str:
        return self.driver.current_url

    def get_title(self) -> str:
        return self.driver.title

    def refresh(self) -> None:
        self.driver.refresh()
        logger.info("刷新页面")

    def back(self) -> None:
        self.driver.back()
        logger.info("浏览器后退")

    def forward(self) -> None:
        self.driver.forward()
        logger.info("浏览器前进")

    # ==================== 等待操作 ====================
    def wait_element_visible(self, locator: Locator, timeout: int | None = None) -> WebElement:
        return WebDriverWait(self.driver, self._timeout(timeout)).until(
            EC.visibility_of_element_located(locator)
        )

    def wait_elements_visible(
        self, locator: Locator, timeout: int | None = None
    ) -> List[WebElement]:
        return WebDriverWait(self.driver, self._timeout(timeout)).until(
            EC.visibility_of_all_elements_located(locator)
        )

    def wait_text_visible(
        self,
        locator: Locator,
        text: str,
        timeout: int | None = None,
    ) -> WebElement:
        wait = WebDriverWait(self.driver, self._timeout(timeout))
        wait.until(EC.text_to_be_present_in_element(locator, text))
        return wait.until(EC.visibility_of_element_located(locator))

    def wait_element_invisible(self, locator: Locator, timeout: int | None = None) -> bool:
        return WebDriverWait(self.driver, self._timeout(timeout)).until(
            EC.invisibility_of_element_located(locator)
        )

    def wait_element_clickable(self, locator: Locator, timeout: int | None = None) -> WebElement:
        return WebDriverWait(self.driver, self._timeout(timeout)).until(
            EC.element_to_be_clickable(locator)
        )

    def wait_url_contains(self, fragment: str, timeout: int | None = None) -> bool:
        return WebDriverWait(self.driver, self._timeout(timeout)).until(EC.url_contains(fragment))

    def wait_url_changes(self, old_url: str, timeout: int | None = None) -> bool:
        return WebDriverWait(self.driver, self._timeout(timeout)).until(EC.url_changes(old_url))

    # ==================== 多窗口操作 ====================
    def switch_to_window_by_index(self, index: int) -> None:
        handles = self.driver.window_handles
        if index >= len(handles):
            raise IndexError(f"窗口索引越界: {index}, 当前窗口数: {len(handles)}")
        self.driver.switch_to.window(handles[index])
        logger.info("切换窗口: index=%s", index)

    def switch_to_window_by_title(self, title: str) -> bool:
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if self.driver.title == title:
                logger.info("切换窗口: title=%s", title)
                return True
        return False

    def get_window_handles(self) -> List[str]:
        return self.driver.window_handles

    def close_current_window(self) -> None:
        self.driver.close()
        logger.info("关闭当前窗口")

    # ==================== Frame操作 ====================
    def switch_to_frame(self, locator: Locator) -> None:
        frame = self.find_element(locator)
        self.driver.switch_to.frame(frame)
        logger.info("切换 iframe: %s", locator)

    def switch_to_default_content(self) -> None:
        self.driver.switch_to.default_content()

    def switch_to_parent_frame(self) -> None:
        self.driver.switch_to.parent_frame()

    # ==================== Alert操作 ====================
    def accept_alert(self, timeout: int = 3) -> None:
        WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
        self.driver.switch_to.alert.accept()

    def dismiss_alert(self, timeout: int = 3) -> None:
        WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
        self.driver.switch_to.alert.dismiss()

    def get_alert_text(self, timeout: int = 3) -> str:
        WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
        return self.driver.switch_to.alert.text

    # ==================== 滚动操作 ====================
    def scroll_to_element(self, locator: Locator) -> None:
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)

    def scroll_to_top(self) -> None:
        self.driver.execute_script("window.scrollTo(0, 0);")

    def scroll_to_bottom(self) -> None:
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

    # ==================== 截图操作 ====================
    def take_screenshot(self, file_path: str) -> None:
        self.driver.save_screenshot(file_path)
        logger.info("截图保存: %s", file_path)
