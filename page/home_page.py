from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

from base.base_page import BasePage


class HomePage(BasePage):
    """短链接系统登录后主布局及“我的空间”页面对象。"""

    _USER_NAME = (By.CSS_SELECTOR, "span.name-span")
    _CREATE_LINK_BUTTON = (
        By.XPATH,
        "//button[.//span[normalize-space()='创建短链']]",
    )
    _BATCH_CREATE_BUTTON = (
        By.XPATH,
        "//button[.//span[normalize-space()='批量创建']]",
    )
    _RECYCLE_BIN = (By.CSS_SELECTOR, ".recycle-box")
    _GROUP_LIST = (By.CSS_SELECTOR, ".options-box .item-box")
    _USER_MENU_TRIGGER = (By.CSS_SELECTOR, ".header .el-dropdown .block")
    _DROPDOWN_ITEMS = (By.CSS_SELECTOR, ".el-dropdown-menu__item")

    def wait_until_loaded(self):
        """等待路由进入 home 子页面并确认登录用户入口已渲染。"""
        self.wait_url_contains("/home/")
        self.wait_element_visible(self._USER_NAME)
        return self

    @staticmethod
    def expected_display_name(username: str, limit: int = 8) -> str:
        """匹配前端头部对用户名超过 8 个字符时的省略展示规则。"""
        return username if len(username) <= limit else username[:limit] + "..."

    def get_user_name(self) -> str:
        return self.get_text(self._USER_NAME)

    def click_create_link(self):
        self.click(self._CREATE_LINK_BUTTON)
        return self

    def click_batch_create(self):
        self.click(self._BATCH_CREATE_BUTTON)
        return self

    def click_recycle_bin(self):
        self.click(self._RECYCLE_BIN)
        return self

    def select_group(self, group_name: str):
        """按已渲染分组名称选择分组，避免把测试数据拼入 XPath。"""
        groups = self.wait_elements_visible(self._GROUP_LIST)
        for group in groups:
            name = group.find_element(By.CSS_SELECTOR, ".over-text").text.strip()
            if name == group_name:
                group.click()
                return self
        raise LookupError(f"未找到短链分组: {group_name}")

    def open_my_space(self):
        """Return the ready group-management page on the default /home/space route."""
        from page.group_page import GroupPage

        self.wait_url_contains("/home/space")
        return GroupPage(self.driver, timeout=self.timeout).wait_until_loaded()

    def is_logged_in(self, timeout: int = 5) -> bool:
        return self.is_visible(self._USER_NAME, timeout=timeout)

    def _click_user_menu_item(self, text: str) -> None:
        trigger = self.wait_element_visible(self._USER_MENU_TRIGGER)
        ActionChains(self.driver).move_to_element(trigger).perform()

        def _item(driver):
            for element in driver.find_elements(*self._DROPDOWN_ITEMS):
                try:
                    if element.is_displayed() and element.text.strip() == text:
                        return element
                except StaleElementReferenceException:
                    continue
            return False

        WebDriverWait(self.driver, self.timeout).until(_item).click()

    def open_account(self):
        """Navigate through the real header dropdown to the account profile page."""
        from page.account_page import AccountPage

        self._click_user_menu_item("个人信息")
        return AccountPage(self.driver, timeout=self.timeout).wait_until_loaded()

    def logout(self):
        """Log out through the real header menu and wait for the login business state."""
        from page.login_page import LoginPage

        self._click_user_menu_item("退出")
        return LoginPage(self.driver, timeout=self.timeout).wait_until_loaded()
