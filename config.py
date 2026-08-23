# config.py
import os

# 项目根路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 测试环境URL
LOGIN_URL = "http://localhost:5174/login"
HOME_URL = "http://localhost:5174/home"

# 日志配置
LOG_DIR = os.path.join(BASE_DIR, "log")
LOG_LEVEL = "INFO"

# 报告配置
REPORT_DIR = os.path.join(BASE_DIR, "report")

# 测试数据路径
DATA_DIR = os.path.join(BASE_DIR, "date")

# 浏览器配置
BROWSER = "edge"
HEADLESS = False
IMPLICITLY_WAIT = 10
EXPLICITLY_WAIT = 10