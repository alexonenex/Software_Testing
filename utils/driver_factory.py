"""
驱动工厂模块
统一管理 Web 浏览器驱动和桌面应用驱动的创建与销毁
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from config.settings import (
    BROWSER, IMPLICIT_WAIT, PAGE_LOAD_TIMEOUT, SCRIPT_TIMEOUT,
    DESKTOP_BACKEND, PARADOX_LAUNCHER_APP, PARADOX_LAUNCHER_PATH,
)
from config.browsers import get_chrome_options, get_firefox_options, get_edge_options
from utils.logger import log


class WebDriverFactory:
    """Web 浏览器驱动工厂"""

    @staticmethod
    def create_driver(browser: str = None) -> webdriver.Remote:
        """
        根据浏览器类型创建 WebDriver 实例
        :param browser: 浏览器类型 (chrome / firefox / edge)
        :return: WebDriver 实例
        """
        browser = browser or BROWSER
        log.info(f"正在启动 {browser} 浏览器...")

        if browser == "chrome":
            driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=get_chrome_options(),
            )
        elif browser == "firefox":
            driver = webdriver.Firefox(
                service=FirefoxService(GeckoDriverManager().install()),
                options=get_firefox_options(),
            )
        elif browser == "edge":
            driver = webdriver.Edge(
                service=EdgeService(EdgeChromiumDriverManager().install()),
                options=get_edge_options(),
            )
        else:
            raise ValueError(f"不支持的浏览器类型: {browser}")

        # 通用配置
        driver.implicitly_wait(IMPLICIT_WAIT)
        driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
        driver.set_script_timeout(SCRIPT_TIMEOUT)
        driver.maximize_window()

        log.info(f"{browser} 浏览器启动成功")
        return driver

    @staticmethod
    def quit_driver(driver: webdriver.Remote):
        """安全关闭浏览器"""
        if driver:
            try:
                driver.quit()
                log.info("浏览器已关闭")
            except Exception as e:
                log.warning(f"关闭浏览器时出错: {e}")


class DesktopDriverFactory:
    """桌面应用驱动工厂（基于 pywinauto）"""

    @staticmethod
    def create_by_app_name(app_name: str = None, backend: str = None):
        """
        通过应用名称连接到已运行的桌面应用
        :param app_name: 应用程序窗口标题
        :param backend: 后端类型 (win32 / uia)
        :return: Application 实例
        """
        from pywinauto import Application

        app_name = app_name or PARADOX_LAUNCHER_APP
        backend = backend or DESKTOP_BACKEND

        log.info(f"正在连接桌面应用: {app_name} (后端: {backend})")
        try:
            app = Application(backend=backend).connect(title_re=f".*{app_name}.*")
            log.info(f"成功连接到桌面应用: {app_name}")
            return app
        except Exception as e:
            log.error(f"连接桌面应用失败: {e}")
            raise

    @staticmethod
    def create_by_path(app_path: str = None, backend: str = None):
        """
        通过路径启动桌面应用
        :param app_path: 应用程序可执行文件路径
        :param backend: 后端类型 (win32 / uia)
        :return: Application 实例
        """
        from pywinauto import Application

        app_path = app_path or PARADOX_LAUNCHER_PATH
        backend = backend or DESKTOP_BACKEND

        log.info(f"正在启动桌面应用: {app_path} (后端: {backend})")
        try:
            app = Application(backend=backend).start(app_path)
            log.info(f"桌面应用启动成功: {app_path}")
            return app
        except Exception as e:
            log.error(f"启动桌面应用失败: {e}")
            raise

    @staticmethod
    def quit_app(app):
        """安全关闭桌面应用"""
        if app:
            try:
                app.kill()
                log.info("桌面应用已关闭")
            except Exception as e:
                log.warning(f"关闭桌面应用时出错: {e}")
