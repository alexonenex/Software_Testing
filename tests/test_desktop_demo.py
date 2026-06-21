"""
桌面应用自动化测试示例
演示使用 pywinauto 对 Paradox Launcher v2 进行测试
"""
import allure
import pytest

from pages.desktop_page import DesktopBasePage
from utils.driver_factory import DesktopDriverFactory
from utils.logger import log


@allure.feature("桌面应用测试")
@allure.story("Paradox Launcher v2")
class TestParadoxLauncher:
    """Paradox Launcher v2 桌面应用测试示例"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """
        初始化桌面应用连接
        注意: 运行此测试前需要先手动启动 Paradox Launcher v2
        """
        try:
            self.app = DesktopDriverFactory.create_by_app_name()
            self.page = DesktopBasePage(self.app)
            self.page.set_window(title_re=".*Paradox.*")
        except Exception as e:
            pytest.skip(f"无法连接到 Paradox Launcher: {e}")

    @allure.title("验证 Paradox Launcher 窗口是否显示")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_launcher_window_visible(self):
        """测试 Paradox Launcher 主窗口是否可见"""
        assert self.page.window is not None, "Launcher 窗口应存在"
        assert self.page.window.is_visible(), "Launcher 窗口应可见"
        log.info("Paradox Launcher 窗口可见性验证通过")

    @allure.title("验证 Paradox Launcher 窗口标题")
    @allure.severity(allure.severity_level.NORMAL)
    def test_launcher_title(self):
        """测试窗口标题包含 Paradox"""
        title = self.page.window.window_text()
        assert "Paradox" in title or "paradox" in title.lower(), \
            f"窗口标题应包含 'Paradox'，实际为: {title}"
        log.info(f"Paradox Launcher 窗口标题: {title}")

    @allure.title("截取 Paradox Launcher 截图")
    @allure.severity(allure.severity_level.MINOR)
    def test_take_launcher_screenshot(self):
        """测试截图功能"""
        self.page.take_screenshot("paradox_launcher")
        log.info("Paradox Launcher 截图测试通过")
