# page/login_page.py
from selenium.webdriver.common.by import By
from base.base_page import BasePage
from config import LOGIN_URL


class LoginPage(BasePage):
    """登录页面对象"""

    # 实例属性：页面元素定位
    USERNAME_INPUT = (By.XPATH, "//input[@placeholder='请输入用户名']")
    PASSWORD_INPUT = (By.XPATH, "//input[@placeholder='请输入密码']")
    LOGIN_BUTTON = (By.XPATH, "//button//span[text()='登录']/..")
    REMEMBER_CHECKBOX = (By.XPATH, "//label//span[@class='el-checkbox__inner']")
    REGISTER_SWITCH = (By.XPATH, "//div[@class='move']//button//span[text()='去注册']/..")
    LOGIN_SWITCH = (By.XPATH, "//div[@class='move']//button//span[text()='去登录']/..")
    ERROR_MSG = (By.CLASS_NAME, "el-message")

    # 实例方法：页面操作
    def open(self):
        """打开登录页面"""
        self.open_url(LOGIN_URL)
        self.maximize_window()
        return self

    def login(self, username: str, password: str, remember: bool = False):
        """登录操作"""
        self.input_text(self.USERNAME_INPUT, username)
        self.input_text(self.PASSWORD_INPUT, password)
        if remember:
            self.click(self.REMEMBER_CHECKBOX)
        self.click(self.LOGIN_BUTTON)
        return self

    def switch_to_register(self):
        """切换到注册表单"""
        self.click(self.REGISTER_SWITCH)
        return self

    def switch_to_login(self):
        """切换到登录表单"""
        self.click(self.LOGIN_SWITCH)
        return self

    def get_error_msg(self) -> str:
        """获取错误提示"""
        return self.get_text(self.ERROR_MSG) if self.is_visible(self.ERROR_MSG) else ""