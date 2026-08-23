# tools.py
import os
import json
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.chrome.options import Options as ChromeOptions
from config import LOG_DIR, BROWSER, HEADLESS, IMPLICITLY_WAIT, DATA_DIR


# ==================== 日志管理 ====================
def get_logger(name="test_log"):
    """获取日志对象"""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    log_file = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if logger.handlers:
        return logger

    # 文件处理器
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


# ==================== 浏览器驱动 ====================
def get_driver():
    """获取浏览器驱动"""
    if BROWSER.lower() == "edge":
        options = EdgeOptions()
        if HEADLESS:
            options.add_argument("--headless")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Edge(options=options)
    elif BROWSER.lower() == "chrome":
        options = ChromeOptions()
        if HEADLESS:
            options.add_argument("--headless")
        options.add_argument("--start-maximized")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        driver = webdriver.Chrome(options=options)
    else:
        raise ValueError(f"不支持的浏览器: {BROWSER}")

    driver.implicitly_wait(IMPLICITLY_WAIT)
    return driver


# ==================== 数据驱动 ====================
def read_json_data(file_name: str):
    """读取JSON测试数据"""
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"数据文件不存在: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)