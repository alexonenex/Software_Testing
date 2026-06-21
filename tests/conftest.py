"""
pytest 全局 fixtures
统一管理测试前置/后置操作
"""
import pytest
import allure

from config.settings import BROWSER
from utils.driver_factory import WebDriverFactory, DesktopDriverFactory
from utils.logger import log


# ==================== 通用钩子 ====================

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """钩子：获取测试结果，用于失败截图"""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


# ==================== Web UI 测试 fixtures ====================

@pytest.fixture(scope="session")
def browser_type():
    """获取浏览器类型，可通过命令行 --browser 传入"""
    return BROWSER


@pytest.fixture(scope="class")
def web_driver(browser_type):
    """
    Web UI 测试的浏览器驱动 fixture
    scope=class: 每个测试类共享一个浏览器实例
    仅在使用 web_driver 的测试类中激活
    """
    driver = WebDriverFactory.create_driver(browser_type)
    yield driver
    WebDriverFactory.quit_driver(driver)


@pytest.fixture(scope="function")
def web_screenshot_on_failure(web_driver, request):
    """
    Web 测试失败时自动截图
    仅在显式依赖 web_driver 的测试中激活（非 autouse）
    """
    yield
    if hasattr(request, "node") and request.node.rep_call.failed:
        import os
        import time
        from config.settings import SCREENSHOTS_DIR
        safe_name = request.node.name.replace("::", "_").replace(" ", "_")
        screenshot_path = os.path.join(SCREENSHOTS_DIR, f"fail_{safe_name}_{int(time.time())}.png")
        try:
            web_driver.save_screenshot(screenshot_path)
            allure.attach.file(screenshot_path, name="failure_screenshot",
                               attachment_type=allure.attachment_type.PNG)
            log.info(f"测试失败截图: {screenshot_path}")
        except Exception as e:
            log.warning(f"截图失败: {e}")


# ==================== 桌面应用测试 fixtures ====================

@pytest.fixture(scope="class")
def desktop_app():
    """
    桌面应用测试 fixture（连接到已运行的 Paradox Launcher）
    如需启动应用，请使用 DesktopDriverFactory.create_by_path()
    """
    app = DesktopDriverFactory.create_by_app_name()
    yield app
    # 不自动关闭桌面应用，避免意外关闭
    # 如需关闭，请在测试中手动调用 DesktopDriverFactory.quit_app(app)


# ==================== API 测试 fixtures ====================

@pytest.fixture(scope="session")
def api_base_url():
    """获取 API 测试基础 URL"""
    from config.settings import API_BASE_URL, ENV
    return API_BASE_URL.get(ENV, API_BASE_URL["test"])


@pytest.fixture(scope="session")
def api_session():
    """
    API 测试的 requests.Session fixture
    复用 TCP 连接，支持统一添加 headers/cookies
    """
    import requests
    session = requests.Session()
    session.headers.update({
        "Content-Type": "application/json",
        "Accept": "application/json",
    })
    yield session
    session.close()