"""
驱动工厂模块
统一管理 Web 浏览器驱动的创建与销毁
"""
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager

from core.settings import BROWSER, IMPLICIT_WAIT, PAGE_LOAD_TIMEOUT, SCRIPT_TIMEOUT
from core.browsers import get_chrome_options, get_firefox_options, get_edge_options
from core.logger import log


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
