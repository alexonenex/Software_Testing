"""
根级 pytest 全局 fixtures
提供所有项目共享的浏览器驱动和通用测试功能
"""
import os
import time

import pytest
import allure

from core.settings import BROWSER, SCREENSHOTS_DIR
from core.driver_factory import WebDriverFactory
from core.logger import log


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
    """获取浏览器类型，可通过环境变量 BROWSER 传入"""
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
        safe_name = request.node.name.replace("::", "_").replace(" ", "_")
        screenshot_path = os.path.join(
            SCREENSHOTS_DIR, f"fail_{safe_name}_{int(time.time())}.png"
        )
        try:
            web_driver.save_screenshot(screenshot_path)
            allure.attach.file(
                screenshot_path,
                name="failure_screenshot",
                attachment_type=allure.attachment_type.PNG,
            )
            log.info(f"测试失败截图: {screenshot_path}")
        except Exception as e:
            log.warning(f"截图失败: {e}")
