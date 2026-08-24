import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


BASE_URL = os.getenv("SHORTLINK_UI_BASE_URL", "http://localhost:5174").rstrip("/")
LOGIN_URL = f"{BASE_URL}/login"
HOME_URL = f"{BASE_URL}/home"

LOG_DIR = str(BASE_DIR / "log")
LOG_LEVEL = os.getenv("SHORTLINK_UI_LOG_LEVEL", "INFO").upper()
REPORT_DIR = str(BASE_DIR / "report")
DATA_DIR = str(BASE_DIR / "date")

BROWSER = os.getenv("SHORTLINK_UI_BROWSER", "edge").strip().lower()
HEADLESS = _env_bool("SHORTLINK_UI_HEADLESS", False)
EXPLICITLY_WAIT = int(os.getenv("SHORTLINK_UI_EXPLICIT_WAIT", "10"))
PAGE_LOAD_TIMEOUT = int(os.getenv("SHORTLINK_UI_PAGE_LOAD_TIMEOUT", "30"))
WINDOW_WIDTH = int(os.getenv("SHORTLINK_UI_WINDOW_WIDTH", "1440"))
WINDOW_HEIGHT = int(os.getenv("SHORTLINK_UI_WINDOW_HEIGHT", "900"))

# Stable redirect target for short-link lifecycle tests; override in local/CI environments.
TARGET_URL = os.getenv("SHORTLINK_UI_TARGET_URL", "https://nageoffer.com/").strip()
