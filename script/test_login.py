# script/test_login.py
import pytest
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools import get_driver, read_json_data, get_logger
from page.login_page import LoginPage
from page.home_page import HomePage
from config import LOGIN_URL

logger = get_logger()


class TestLogin:
    """登录功能测试类"""

    def setup_method(self):
        self.driver = get_driver()
        self.login_page = LoginPage(self.driver)
        self.home_page = HomePage(self.driver)
        self.login_page.open()
        logger.info("=" * 50)
        logger.info("开始执行测试用例")

    def teardown_method(self):
        import time
        time.sleep(3)
        self.driver.quit()
        logger.info("测试用例执行结束")
        logger.info("=" * 50)

    @pytest.mark.parametrize("test_data", read_json_data("login_data.json"))
    def test_login(self, test_data):
        username = test_data["username"]
        password = test_data["password"]
        remember = test_data.get("remember", False)
        expected = test_data["expected"]

        self.login_page.login(username, password, remember)

        current_url = self.login_page.get_url()
        logger.info(f"用户名: {username}, 期望结果: {expected}, 当前URL: {current_url}")

        if expected == "success":
            assert current_url != LOGIN_URL
            logger.info(f"✅ 登录成功: {username}")
        else:
            assert LOGIN_URL in current_url
            logger.info(f"✅ 登录失败: {username}")

    def test_switch_to_register(self):
        self.login_page.switch_to_register()
        assert self.login_page.is_visible(self.login_page.REGISTER_SWITCH)
        logger.info("✅ 切换到注册表单测试通过")

    def test_switch_to_login(self):
        self.login_page.switch_to_register()
        self.login_page.switch_to_login()
        assert self.login_page.is_visible(self.login_page.LOGIN_BUTTON)
        logger.info("✅ 切换到登录表单测试通过")