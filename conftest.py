from __future__ import annotations

import platform
from pathlib import Path

import pytest

from tools import get_logger, read_json_data

logger = get_logger()

try:
    import allure
except ImportError:  # Allows non-Allure tooling to import the test project.
    allure = None


_ALLURE_FEATURE_PREFIXES = (
    ("tests/ui/authentication/", "Authentication"),
    ("tests/ui/group/", "Group"),
    ("tests/ui/link/", "Short Link"),
    ("tests/ui/recycle/", "Recycle Bin"),
    ("tests/ui/account/", "Account"),
    ("tests/e2e/", "Cross-domain E2E"),
)


def _allure_feature_for_nodeid(nodeid: str) -> str | None:
    normalized = nodeid.replace("\\", "/")
    for prefix, feature in _ALLURE_FEATURE_PREFIXES:
        if normalized.startswith(prefix):
            return feature
    return None


def _allure_story_for_nodeid(nodeid: str) -> str:
    test_path = nodeid.split("::", 1)[0].replace("\\", "/")
    stem = Path(test_path).stem
    if stem.startswith("test_"):
        stem = stem[5:]
    return stem.replace("_", " ").title()


def _allure_environment_properties() -> dict[str, str]:
    from config import BASE_URL, BROWSER, HEADLESS

    os_name = " ".join(part for part in (platform.system(), platform.release()) if part)
    return {
        "Browser": BROWSER,
        "Base_URL": BASE_URL,
        "Headless": str(HEADLESS).lower(),
        "Python": platform.python_version(),
        "OS": os_name,
    }


def _write_allure_environment(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    properties = _allure_environment_properties()
    content = "\n".join(f"{key}={value}" for key, value in properties.items()) + "\n"
    path.write_text(content, encoding="utf-8")


@pytest.fixture(autouse=True)
def _allure_business_hierarchy(request):
    """Apply Allure business labels centrally without leaking reporting into tests."""
    if allure is None:
        return

    feature = _allure_feature_for_nodeid(request.node.nodeid)
    if feature is None:
        return

    story = _allure_story_for_nodeid(request.node.nodeid)
    allure.dynamic.epic("Shortlink UI Automation")
    allure.dynamic.feature(feature)
    allure.dynamic.story(story)


def _known_success_user() -> dict | None:
    try:
        cases = read_json_data("login_data.json")
    except FileNotFoundError:
        return None
    for case in cases:
        if case.get("expected") == "success" and case.get("username") and case.get("password"):
            return case
    return None


@pytest.fixture
def driver():
    """Own one browser lifecycle per UI test."""
    from core.driver_factory import create_driver

    driver = create_driver()
    try:
        yield driver
    finally:
        driver.quit()


@pytest.fixture
def login_page(driver):
    from page.login_page import LoginPage

    return LoginPage(driver).open()


@pytest.fixture
def home_page(driver):
    from page.home_page import HomePage

    return HomePage(driver)


@pytest.fixture
def authenticated_home_page(driver):
    """Log in through the real UI and expose the authenticated home shell."""
    from page.home_page import HomePage
    from page.login_page import LoginPage

    user = _known_success_user()
    if user is None:
        pytest.skip("本地 login_data.json 中没有 expected=success 的真实账号")

    LoginPage(driver).open().login(
        user["username"],
        user["password"],
        user.get("remember", False),
    )
    return HomePage(driver).wait_until_loaded()


@pytest.fixture
def authenticated_group_page(authenticated_home_page):
    """Expose the ready My Space group page after real UI authentication."""
    return authenticated_home_page.open_my_space()


@pytest.fixture
def account_profile_context(authenticated_home_page):
    """Own one reversible account-profile edit and restore the original mail through UI."""
    from types import SimpleNamespace

    page = authenticated_home_page.open_account()
    original_profile = page.get_profile()
    context = SimpleNamespace(page=page, original_profile=original_profile, restored=False)
    try:
        yield context
    finally:
        page.close_edit_dialog_if_open()
        if not context.restored and page.get_profile().mail != original_profile.mail:
            page.update_mail(original_profile.mail)


@pytest.fixture
def temporary_group(authenticated_group_page):
    """Create one active UI group and soft-delete it during teardown if still owned."""
    from utils.test_data_factory import build_group_data

    resource = build_group_data()
    authenticated_group_page.create_group(resource.name)
    try:
        yield resource
    finally:
        if resource.active and authenticated_group_page.has_group(resource.name):
            authenticated_group_page.delete_group(resource.name)
            resource.active = False


@pytest.fixture
def temporary_group_pair(authenticated_group_page):
    """Create two independent groups and clean both active resources in reverse order."""
    from utils.test_data_factory import build_group_data

    resources = [build_group_data(), build_group_data()]
    for resource in resources:
        authenticated_group_page.create_group(resource.name)
    try:
        yield resources
    finally:
        for resource in reversed(resources):
            if resource.active and authenticated_group_page.has_group(resource.name):
                authenticated_group_page.delete_group(resource.name)
                resource.active = False


@pytest.fixture
def temporary_link_context(authenticated_group_page):
    """Own one unique group and expose a ready LinkPage for short-link scenarios."""
    from types import SimpleNamespace

    from page.link_page import LinkPage
    from utils.test_data_factory import build_group_data

    group = build_group_data(prefix="ui-lg")
    authenticated_group_page.create_group(group.name)
    authenticated_group_page.select_group(group.name)
    link_page = LinkPage(authenticated_group_page.driver, timeout=authenticated_group_page.timeout).wait_until_loaded()
    context = SimpleNamespace(page=link_page, group=group, group_page=authenticated_group_page)
    try:
        yield context
    finally:
        if group.active and authenticated_group_page.has_group(group.name):
            authenticated_group_page.delete_group(group.name)
            group.active = False


@pytest.fixture
def temporary_link(temporary_link_context):
    """Create one UI-owned short link and move it to recycle during teardown if still active."""
    from types import SimpleNamespace

    from utils.test_data_factory import build_link_data

    page = temporary_link_context.page
    link = build_link_data()
    try:
        page.create_link(link.origin_url, link.description)
    except Exception:
        if page.has_link(link.description):
            page.move_link_to_recycle(link.description)
            link.active = False
        raise

    context = SimpleNamespace(
        page=page,
        group=temporary_link_context.group,
        group_page=temporary_link_context.group_page,
        link=link,
    )
    try:
        yield context
    finally:
        if link.active and page.has_link(link.description):
            page.move_link_to_recycle(link.description)
            link.active = False


@pytest.fixture
def temporary_recycle_link(temporary_link):
    """Own one short link and permanently clean it through the recycle-bin UI."""
    context = temporary_link
    page = context.page
    link = context.link
    group_page = context.group_page
    group = context.group

    try:
        yield context
    finally:
        group_page.select_group(group.name)
        page.wait_until_loaded()
        if page.has_link(link.description, timeout=2):
            page.move_link_to_recycle(link.description)
        link.active = False

        page.open_recycle_bin()
        if page.has_link(link.description, timeout=2):
            page.permanently_delete_link(link.description)


@pytest.fixture
def known_success_user():
    """Expose the configured real account without hiding login actions from E2E workflows."""
    user = _known_success_user()
    if user is None:
        pytest.skip("本地 login_data.json 中没有 expected=success 的真实账号")
    return user


class _E2ECleanupRegistry:
    """Track only E2E-owned mutable resources for UI-only failure cleanup."""

    def __init__(self, driver, user: dict):
        self.driver = driver
        self.user = user
        self.groups = []
        self.links = []
        self.profile_mail = None

    def track_group(self, group):
        if group not in self.groups:
            self.groups.append(group)
        return group

    def forget_group(self, group) -> None:
        if group in self.groups:
            self.groups.remove(group)

    def track_link(self, group, link):
        entry = (group, link)
        if entry not in self.links:
            self.links.append(entry)
        return link

    def forget_link(self, link) -> None:
        self.links = [(group, item) for group, item in self.links if item is not link]

    def track_profile_mail(self, original_mail: str) -> None:
        self.profile_mail = original_mail

    def clear_profile_mail(self) -> None:
        self.profile_mail = None

    def has_pending_cleanup(self) -> bool:
        return bool(self.groups or self.links or self.profile_mail is not None)

    def cleanup(self) -> None:
        if not self.has_pending_cleanup():
            return

        from config import HOME_URL
        from page.home_page import HomePage
        from page.link_page import LinkPage
        from page.login_page import LoginPage

        navigator = LoginPage(self.driver)
        navigator.open_url(f"{HOME_URL}/space")
        if "/login" in navigator.get_url():
            navigator.wait_until_loaded().login(
                self.user["username"],
                self.user["password"],
                self.user.get("remember", False),
            )

        home = HomePage(self.driver).wait_until_loaded()
        group_page = home.open_my_space()
        link_page = LinkPage(self.driver, timeout=group_page.timeout).wait_until_loaded()

        for group, link in list(self.links):
            if group_page.has_group(group.name, timeout=2):
                group_page.select_group(group.name)
                link_page.wait_until_loaded()
                if link_page.has_link(link.description, timeout=1):
                    link_page.move_link_to_recycle(link.description)

            link_page.open_recycle_bin()
            if link_page.has_link(link.description, timeout=1):
                link_page.permanently_delete_link(link.description)
            self.forget_link(link)

        for group in list(reversed(self.groups)):
            if group_page.has_group(group.name, timeout=2):
                group_page.select_group(group.name)
                group_page.delete_group(group.name)
            self.forget_group(group)

        if self.profile_mail is not None:
            account = HomePage(self.driver).open_account()
            if account.get_profile().mail != self.profile_mail:
                account.update_mail(self.profile_mail)
            self.clear_profile_mail()


@pytest.fixture
def e2e_cleanup(driver, known_success_user):
    """Safety net for resources left behind when an E2E workflow aborts mid-flight."""
    registry = _E2ECleanupRegistry(driver, known_success_user)
    try:
        yield registry
    finally:
        registry.cleanup()


def pytest_sessionfinish(session, exitstatus):
    """Write non-secret runtime metadata beside Allure result files."""
    if allure is None:
        return

    from config import REPORT_DIR

    _write_allure_environment(Path(REPORT_DIR) / "environment.properties")


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Attach a browser screenshot to Allure when a UI test fails."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return

    driver = item.funcargs.get("driver")
    if driver is None or allure is None:
        return

    try:
        png = driver.get_screenshot_as_png()
        allure.attach(
            png,
            name=f"{item.name}-failure",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception as exc:  # Screenshot failure must not replace the test verdict.
        logger.warning("失败截图采集失败: %s", exc)
