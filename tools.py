import json
import logging
import os
from datetime import datetime

from config import DATA_DIR, LOG_DIR, LOG_LEVEL


def get_logger(name: str = "shortlink_ui") -> logging.Logger:
    """Return a process-local logger without duplicating handlers."""
    os.makedirs(LOG_DIR, exist_ok=True)
    log_file = os.path.join(LOG_DIR, f"{datetime.now().strftime('%Y%m%d')}.log")

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, LOG_LEVEL, logging.INFO))
    if logger.handlers:
        return logger

    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    return logger


def read_json_data(file_name: str):
    """Read one local JSON test-data file from the configured data directory."""
    file_path = os.path.join(DATA_DIR, file_name)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"数据文件不存在: {file_path}")
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)
