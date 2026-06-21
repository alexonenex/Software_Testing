"""
浏览器配置
集中管理不同浏览器的启动选项
"""
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions

from config.settings import HEADLESS, WINDOW_SIZE


def get_chrome_options() -> ChromeOptions:
    """获取 Chrome 浏览器配置"""
    options = ChromeOptions()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={WINDOW_SIZE[0]},{WINDOW_SIZE[1]}")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    # 禁用密码保存提示
    prefs = {
        "credentials_enable_service": False,
        "profile.password_manager_enabled": False,
    }
    options.add_experimental_option("prefs", prefs)
    return options


def get_firefox_options() -> FirefoxOptions:
    """获取 Firefox 浏览器配置"""
    options = FirefoxOptions()
    if HEADLESS:
        options.add_argument("--headless")
    options.add_argument(f"--width={WINDOW_SIZE[0]}")
    options.add_argument(f"--height={WINDOW_SIZE[1]}")
    return options


def get_edge_options() -> EdgeOptions:
    """获取 Edge 浏览器配置"""
    options = EdgeOptions()
    if HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={WINDOW_SIZE[0]},{WINDOW_SIZE[1]}")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    return options
