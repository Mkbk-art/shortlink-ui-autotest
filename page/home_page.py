# page/home_page.py
from selenium.webdriver.common.by import By
from base.base_page import BasePage


class HomePage(BasePage):
    """首页对象"""

    # 实例属性：页面元素定位
    USER_NAME = (By.XPATH, "//span[@class='name-span']")
    CREATE_LINK_BTN = (By.XPATH, "//button//span[text()='创建短链']/..")
    BATCH_CREATE_BTN = (By.XPATH, "//button//span[text()='批量创建']/..")
    RECYCLE_BIN = (By.XPATH, "//div[@class='recycle-box']")
    GROUP_LIST = (By.CSS_SELECTOR, ".options-box .item-box")

    # 实例方法：页面操作
    def get_user_name(self) -> str:
        """获取用户名"""
        return self.get_text(self.USER_NAME)

    def click_create_link(self):
        """点击创建短链"""
        self.click(self.CREATE_LINK_BTN)
        return self

    def click_batch_create(self):
        """点击批量创建"""
        self.click(self.BATCH_CREATE_BTN)
        return self

    def click_recycle_bin(self):
        """点击回收站"""
        self.click(self.RECYCLE_BIN)
        return self

    def select_group(self, group_name: str):
        """选择分组"""
        locator = (By.XPATH, f"//div[@class='flex-box']//span[text()='{group_name}']")
        self.click(locator)
        return self

    def is_logged_in(self) -> bool:
        """判断是否已登录"""
        return self.is_visible(self.USER_NAME)