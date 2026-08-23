# base/base_page.py
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException
from typing import List, Tuple
from tools import get_logger

logger = get_logger()


class BasePage:
    """页面基类 - 封装所有页面共用的公共操作方法"""

    def __init__(self, driver):
        self.driver = driver
        self.timeout = 10

    # ==================== 元素定位 ====================
    def find_element(self, locator: Tuple[str, str], timeout: int = None) -> WebElement:
        """定位单个元素"""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located(locator)
        )

    def find_elements(self, locator: Tuple[str, str], timeout: int = None) -> List[WebElement]:
        """定位一组元素"""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_all_elements_located(locator)
        )

    # ==================== 元素操作 ====================
    def click(self, locator: Tuple[str, str], timeout: int = None) -> None:
        """点击元素"""
        timeout = timeout or self.timeout
        element = WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )
        element.click()
        logger.info(f"点击: {locator}")

    def input_text(self, locator: Tuple[str, str], text: str, clear_first: bool = True) -> None:
        """输入文本"""
        element = self.find_element(locator)
        if clear_first:
            element.clear()
        element.send_keys(text)
        logger.info(f"输入: {locator} -> {text}")

    def get_text(self, locator: Tuple[str, str]) -> str:
        """获取元素文本"""
        return self.find_element(locator).text

    def get_attribute(self, locator: Tuple[str, str], attribute: str) -> str:
        """获取元素属性"""
        return self.find_element(locator).get_attribute(attribute)

    # ==================== 元素状态 ====================
    def is_visible(self, locator: Tuple[str, str], timeout: int = 3) -> bool:
        """判断元素是否可见"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    def is_clickable(self, locator: Tuple[str, str], timeout: int = 3) -> bool:
        """判断元素是否可点击"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            return True
        except TimeoutException:
            return False

    def is_selected(self, locator: Tuple[str, str]) -> bool:
        """判断复选框/单选框是否选中"""
        return self.find_element(locator).is_selected()

    # ==================== 浏览器操作 ====================
    def open_url(self, url: str) -> None:
        """打开URL"""
        self.driver.get(url)
        logger.info(f"打开: {url}")

    def get_url(self) -> str:
        """获取当前页面URL"""
        return self.driver.current_url

    def get_title(self) -> str:
        """获取当前页面标题"""
        return self.driver.title

    def refresh(self) -> None:
        """刷新页面"""
        self.driver.refresh()
        logger.info("刷新页面")

    def back(self) -> None:
        """后退"""
        self.driver.back()
        logger.info("后退")

    def forward(self) -> None:
        """前进"""
        self.driver.forward()
        logger.info("前进")

    def maximize_window(self) -> None:
        """最大化窗口"""
        self.driver.maximize_window()
        logger.info("窗口最大化")

    # ==================== 等待操作 ====================
    def wait_element_visible(self, locator: Tuple[str, str], timeout: int = None) -> WebElement:
        """等待元素可见"""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located(locator)
        )

    def wait_element_invisible(self, locator: Tuple[str, str], timeout: int = None) -> bool:
        """等待元素不可见"""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located(locator)
        )

    def wait_element_clickable(self, locator: Tuple[str, str], timeout: int = None) -> WebElement:
        """等待元素可点击"""
        timeout = timeout or self.timeout
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable(locator)
        )

    # ==================== 多窗口操作 ====================
    def switch_to_window_by_index(self, index: int) -> None:
        """切换到指定索引的窗口"""
        handles = self.driver.window_handles
        if index < len(handles):
            self.driver.switch_to.window(handles[index])
            logger.info(f"切换到第{index}个窗口")

    def switch_to_window_by_title(self, title: str) -> bool:
        """切换到指定标题的窗口"""
        for handle in self.driver.window_handles:
            self.driver.switch_to.window(handle)
            if self.driver.title == title:
                logger.info(f"切换到标题: {title}")
                return True
        return False

    def get_window_handles(self) -> List[str]:
        """获取所有窗口句柄"""
        return self.driver.window_handles

    def close_current_window(self) -> None:
        """关闭当前窗口"""
        self.driver.close()
        logger.info("关闭当前窗口")

    # ==================== Frame操作 ====================
    def switch_to_frame(self, locator: Tuple[str, str]) -> None:
        """切换到指定iframe"""
        frame = self.find_element(locator)
        self.driver.switch_to.frame(frame)
        logger.info(f"切换到iframe: {locator}")

    def switch_to_default_content(self) -> None:
        """切换到主文档"""
        self.driver.switch_to.default_content()
        logger.info("切换到主文档")

    def switch_to_parent_frame(self) -> None:
        """切换到父级iframe"""
        self.driver.switch_to.parent_frame()
        logger.info("切换到父级iframe")

    # ==================== Alert操作 ====================
    def accept_alert(self, timeout: int = 3) -> None:
        """接受弹窗"""
        WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
        self.driver.switch_to.alert.accept()
        logger.info("接受弹窗")

    def dismiss_alert(self, timeout: int = 3) -> None:
        """取消弹窗"""
        WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
        self.driver.switch_to.alert.dismiss()
        logger.info("取消弹窗")

    def get_alert_text(self, timeout: int = 3) -> str:
        """获取弹窗文本"""
        WebDriverWait(self.driver, timeout).until(EC.alert_is_present())
        return self.driver.switch_to.alert.text

    # ==================== 滚动操作 ====================
    def scroll_to_element(self, locator: Tuple[str, str]) -> None:
        """滚动到指定元素"""
        element = self.find_element(locator)
        self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
        logger.info(f"滚动到元素: {locator}")

    def scroll_to_top(self) -> None:
        """滚动到顶部"""
        self.driver.execute_script("window.scrollTo(0, 0);")
        logger.info("滚动到顶部")

    def scroll_to_bottom(self) -> None:
        """滚动到底部"""
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        logger.info("滚动到底部")

    # ==================== 截图操作 ====================
    def take_screenshot(self, file_path: str) -> None:
        """截图"""
        self.driver.save_screenshot(file_path)
        logger.info(f"截图保存: {file_path}")