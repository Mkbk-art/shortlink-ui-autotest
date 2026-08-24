from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def _text(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def test_local_login_data_stays_private_and_public_example_is_placeholder_only():
    example_path = ROOT / "date" / "login_data.example.json"
    assert example_path.is_file()

    data = json.loads(example_path.read_text(encoding="utf-8"))
    assert data == [
        {
            "username": "replace-with-valid-username",
            "password": "replace-with-valid-password",
            "remember": False,
            "expected": "success",
        }
    ]

    gitignore = _text(".gitignore")
    assert "/date/login_data.json" in gitignore
    assert "login_data.example.json" not in gitignore


def test_runtime_private_and_local_tooling_paths_are_ignored():
    gitignore = _text(".gitignore")
    for token in (
        "__pycache__/",
        ".pytest_cache/",
        ".idea/",
        "log/",
        "report/",
        "allure-results/",
        "allure-report/",
        ".env",
        "/date/login_data.json",
    ):
        assert token in gitignore


def test_public_repository_does_not_vendor_sut_or_interview_material():
    forbidden_top_level = {
        "frontend",
        "front-end",
        "backend",
        "back-end",
        "sut",
        "interview",
        "面试",
    }
    actual = {path.name.lower() for path in ROOT.iterdir() if path.is_dir()}
    assert actual.isdisjoint(forbidden_top_level)


def test_allure_business_hierarchy_is_centralized_and_browser_tests_stay_clean():
    conftest_source = _text("conftest.py")
    assert "def _allure_feature_for_nodeid(" in conftest_source
    assert "def _allure_story_for_nodeid(" in conftest_source
    assert "@pytest.fixture(autouse=True)" in conftest_source
    assert 'allure.dynamic.epic("Shortlink UI Automation")' in conftest_source
    assert "allure.dynamic.feature(feature)" in conftest_source
    assert "allure.dynamic.story(story)" in conftest_source

    for root in (ROOT / "tests" / "ui", ROOT / "tests" / "e2e"):
        for path in root.rglob("test_*.py"):
            source = path.read_text(encoding="utf-8")
            assert "import allure" not in source
            assert "allure." not in source


def test_allure_feature_and_story_mapping_cover_all_browser_domains():
    import conftest as project_conftest

    assert hasattr(project_conftest, "_allure_feature_for_nodeid")
    assert hasattr(project_conftest, "_allure_story_for_nodeid")

    cases = {
        "tests/ui/authentication/test_login.py::TestLogin::test_login_success": ("Authentication", "Login"),
        "tests/ui/group/test_group_lifecycle.py::TestGroup::test_group_create_and_select": ("Group", "Group Lifecycle"),
        "tests/ui/link/test_link_creation.py::TestLink::test_link_create_and_list_visibility": ("Short Link", "Link Creation"),
        "tests/ui/recycle/test_recycle_lifecycle.py::TestRecycleLifecycle::test_link_moves_to_recycle_and_appears_in_recycle_bin": ("Recycle Bin", "Recycle Lifecycle"),
        "tests/ui/account/test_account_profile.py::TestAccountProfile::test_account_profile_mail_update_and_restore": ("Account", "Account Profile"),
        "tests/e2e/test_shortlink_lifecycle.py::test_complete_shortlink_lifecycle": ("Cross-domain E2E", "Shortlink Lifecycle"),
    }
    for nodeid, expected in cases.items():
        assert project_conftest._allure_feature_for_nodeid(nodeid) == expected[0]
        assert project_conftest._allure_story_for_nodeid(nodeid) == expected[1]

    assert project_conftest._allure_feature_for_nodeid("tests/contract/test_account_contract.py::test_x") is None


def test_allure_environment_metadata_contains_runtime_context_without_credentials(tmp_path):
    import conftest as project_conftest

    assert hasattr(project_conftest, "_allure_environment_properties")
    assert hasattr(project_conftest, "_write_allure_environment")

    properties = project_conftest._allure_environment_properties()
    assert set(properties) == {"Browser", "Base_URL", "Headless", "Python", "OS"}
    assert properties["Browser"]
    assert properties["Base_URL"].startswith(("http://", "https://"))
    assert properties["Headless"] in {"true", "false"}
    assert properties["Python"]
    assert properties["OS"]

    lowered = "\n".join(f"{key}={value}" for key, value in properties.items()).lower()
    for forbidden in ("username", "password", "token", "secret"):
        assert forbidden not in lowered

    output = tmp_path / "environment.properties"
    project_conftest._write_allure_environment(output)
    written = output.read_text(encoding="utf-8")
    for key, value in properties.items():
        assert f"{key}={value}" in written


def test_github_actions_runs_only_offline_contract_tests_on_python_311():
    workflow_path = ROOT / ".github" / "workflows" / "contract-tests.yml"
    assert workflow_path.is_file()

    source = workflow_path.read_text(encoding="utf-8")
    assert "push:" in source
    assert "pull_request:" in source
    assert "actions/checkout@v4" in source
    assert "actions/setup-python@v5" in source
    assert 'python-version: "3.11"' in source
    assert "pip install -r requirements.txt" in source
    assert "pytest -q tests/contract" in source
    assert "tests/ui" not in source
    assert "tests/e2e" not in source


def test_readme_presents_architecture_coverage_stability_and_public_boundary():
    readme_path = ROOT / "README.md"
    assert readme_path.is_file()
    source = readme_path.read_text(encoding="utf-8")

    required_terms = (
        "Shortlink UI Automation",
        "SUT (System Under Test)",
        "Contract tests",
        "Module-level UI tests",
        "Cross-domain E2E",
        "Page Object",
        "Explicit Wait",
        "UI-only cleanup",
        "Allure",
        "Known SUT Issues",
        "Statistics",
        "GitHub Actions",
        "Repository Boundary",
    )
    for term in required_terms:
        assert term in source

    assert "34" in source
    assert "6" in source
    assert "40" in source
    assert "38 passed" in source
    assert "2 xfailed" in source
    assert "pytest -q tests/contract" in source
    assert "pytest -v -s tests/ui tests/e2e" in source
    assert "allure serve report" in source


def test_readme_documents_all_six_cross_domain_workflows_without_publishing_interview_notes():
    source = _text("README.md")
    for workflow in (
        "Complete Shortlink Lifecycle",
        "Group-Link Isolation",
        "Short URL Identity",
        "Recycle Recovery Ownership",
        "Session Lifecycle",
        "Profile Persistence",
    ):
        assert workflow in source

    for forbidden in ("面试话术", "STAR 回答", "简历措辞", "面试复盘"):
        assert forbidden not in source


def test_sut_setup_document_uses_separate_sut_and_lists_supported_runtime_configuration():
    setup_path = ROOT / "docs" / "sut-setup.md"
    assert setup_path.is_file()
    source = setup_path.read_text(encoding="utf-8")

    assert "date/login_data.example.json" in source
    assert "date/login_data.json" in source
    assert "http://localhost:5174" in source
    for env_name in (
        "SHORTLINK_UI_BASE_URL",
        "SHORTLINK_UI_BROWSER",
        "SHORTLINK_UI_HEADLESS",
        "SHORTLINK_UI_EXPLICIT_WAIT",
        "SHORTLINK_UI_PAGE_LOAD_TIMEOUT",
        "SHORTLINK_UI_WINDOW_WIDTH",
        "SHORTLINK_UI_WINDOW_HEIGHT",
        "SHORTLINK_UI_TARGET_URL",
    ):
        assert env_name in source

    lowered = source.lower()
    assert "frontend source" in lowered
    assert "backend source" in lowered
    assert "replace-with-valid-password" not in source
