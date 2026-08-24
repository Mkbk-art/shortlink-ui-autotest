# SUT Setup

本仓库是独立的 Shortlink UI automation project，只提供测试工程，不提供被测业务系统源码。

- **frontend source**：不包含在本仓库。
- **backend source**：不包含在本仓库。

运行浏览器 UI / E2E tests 前，需要自行准备一个已经启动、可访问的 Shortlink **SUT (System Under Test)**。

## 1. SUT 可访问性

默认 Web frontend 地址：

```text
http://localhost:5174
```

如果实际环境不同，通过环境变量覆盖：

```bash
SHORTLINK_UI_BASE_URL=http://your-shortlink-host
```

测试通过浏览器访问 deployed SUT；运行时不需要 frontend/backend source directory。

## 2. 安装 Python 依赖

建议 Python 3.11：

```bash
python -m venv .venv
```

激活环境后：

```bash
pip install -r requirements.txt
```

默认浏览器是 Microsoft Edge。项目同时支持 Chrome，WebDriver 由 Selenium Manager 处理。

## 3. 配置本地真实账号

仓库只提交：

```text
date/login_data.example.json
```

复制为本地文件：

```bash
cp date/login_data.example.json date/login_data.json
```

Windows PowerShell 也可以使用：

```powershell
Copy-Item date/login_data.example.json date/login_data.json
```

然后把 `date/login_data.json` 中的 username/password 替换为当前 SUT 可登录的测试账号。

至少需要保留一条：

```json
{
  "username": "<valid-test-user>",
  "password": "<local-only-password>",
  "remember": false,
  "expected": "success"
}
```

`date/login_data.json` 已在 `.gitignore` 中排除，不应提交到 Git。

## 4. Runtime configuration

项目当前支持以下环境变量：

| Variable | Default | Purpose |
| --- | --- | --- |
| `SHORTLINK_UI_BASE_URL` | `http://localhost:5174` | Web frontend base URL |
| `SHORTLINK_UI_BROWSER` | `edge` | `edge` / `chrome` |
| `SHORTLINK_UI_HEADLESS` | `false` | 是否使用 headless browser |
| `SHORTLINK_UI_EXPLICIT_WAIT` | `10` | Explicit Wait timeout（秒） |
| `SHORTLINK_UI_PAGE_LOAD_TIMEOUT` | `30` | Page load timeout（秒） |
| `SHORTLINK_UI_WINDOW_WIDTH` | `1440` | Headless viewport width |
| `SHORTLINK_UI_WINDOW_HEIGHT` | `900` | Headless viewport height |
| `SHORTLINK_UI_TARGET_URL` | `https://nageoffer.com/` | Short-link create/redirect 的默认真实 target |

例如 Git Bash：

```bash
export SHORTLINK_UI_BASE_URL=http://localhost:5174
export SHORTLINK_UI_BROWSER=edge
export SHORTLINK_UI_HEADLESS=false
```

PowerShell：

```powershell
$env:SHORTLINK_UI_BASE_URL = "http://localhost:5174"
$env:SHORTLINK_UI_BROWSER = "edge"
$env:SHORTLINK_UI_HEADLESS = "false"
```

`SHORTLINK_UI_TARGET_URL` 用于需要真实网页 metadata / redirect 的测试。如果默认 target 在当前网络不可访问，可以显式替换为一个稳定、允许访问的 HTTP/HTTPS 地址。

## 5. 验证环境

先运行完全离线的 Contract tests：

```bash
pytest -q tests/contract
```

再进行一个真实浏览器登录验证：

```bash
pytest -v -s tests/ui/authentication/test_login.py::TestLogin::test_login_success
```

确认 SUT、浏览器和账号环境正确后，再运行完整 Browser regression：

```bash
pytest -v -s tests/ui tests/e2e
```

## 6. Allure

正常 pytest 配置会把 Allure results 写入：

```text
report/
```

查看报告：

```bash
allure serve report
```

Allure Commandline 需要单独安装。报告的 environment metadata 只记录 Browser、Base URL、Headless、Python 和 OS，不记录账号、密码或 token。

## 7. Public repository boundary

本仓库用于展示 automation engineering，不用于分发 SUT：

```text
automation repository
        ↓
Selenium + browser
        ↓
separately deployed Shortlink SUT
```

因此无需把业务系统源代码复制进本仓库，也不应为了让 GitHub Actions 跑 Browser tests 而上传真实账号或私有后端配置。
