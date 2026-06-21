"""
Web 页面基类
封装 Selenium WebDriver 的常用操作，实现 Page Object 模式
"""
import os
import time

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    ElementNotInteractableException,
)

from config.settings import SCREENSHOTS_DIR, IMPLICIT_WAIT
from utils.logger import log


class BasePage:
    """Web 页面基类，所有页面类应继承此类"""

    def __init__(self, driver):
        self.driver = driver
        self.wait = WebDriverWait(driver, IMPLICIT_WAIT)

    # ==================== 元素定位 ====================

    def find_element(self, locator: tuple, timeout: int = None):
        """
        查找单个元素（显式等待）
        :param locator: 定位器元组，如 (By.ID, "username")
        :param timeout: 超时时间（秒）
        :return: WebElement
        """
        timeout = timeout or IMPLICIT_WAIT
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(locator)
            )
            return element
        except TimeoutException:
            log.error(f"元素定位超时: {locator}")
            self.take_screenshot(f"element_timeout_{int(time.time())}")
            raise

    def find_elements(self, locator: tuple, timeout: int = None):
        """
        查找多个元素
        :param locator: 定位器元组
        :param timeout: 超时时间（秒）
        :return: WebElement 列表
        """
        timeout = timeout or IMPLICIT_WAIT
        try:
            elements = WebDriverWait(self.driver, timeout).until(
                EC.presence_of_all_elements_located(locator)
            )
            return elements
        except TimeoutException:
            log.error(f"元素定位超时: {locator}")
            raise

    # ==================== 元素操作 ====================

    def click(self, locator: tuple, timeout: int = None):
        """点击元素"""
        timeout = timeout or IMPLICIT_WAIT
        try:
            element = WebDriverWait(self.driver, timeout).until(
                EC.element_to_be_clickable(locator)
            )
            element.click()
            log.debug(f"点击元素: {locator}")
        except ElementNotInteractableException:
            # 尝试 JS 点击
            self.driver.execute_script("arguments[0].click();", self.find_element(locator))
            log.debug(f"JS 点击元素: {locator}")

    def input_text(self, locator: tuple, text: str, clear: bool = True):
        """输入文本"""
        element = self.find_element(locator)
        if clear:
            element.clear()
        element.send_keys(text)
        log.debug(f"输入文本: {locator} -> '{text}'")

    def get_text(self, locator: tuple) -> str:
        """获取元素文本"""
        element = self.find_element(locator)
        return element.text

    def get_attribute(self, locator: tuple, attribute: str) -> str:
        """获取元素属性"""
        element = self.find_element(locator)
        return element.get_attribute(attribute)

    def is_element_visible(self, locator: tuple, timeout: int = 5) -> bool:
        """判断元素是否可见"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.visibility_of_element_located(locator)
            )
            return True
        except TimeoutException:
            return False

    # ==================== 页面操作 ====================

    def open_url(self, url: str):
        """打开 URL"""
        self.driver.get(url)
        log.info(f"打开页面: {url}")

    def get_current_url(self) -> str:
        """获取当前 URL"""
        return self.driver.current_url

    def get_page_title(self) -> str:
        """获取页面标题"""
        return self.driver.title

    def wait_for_url_contains(self, text: str, timeout: int = None):
        """等待 URL 包含指定文本"""
        timeout = timeout or IMPLICIT_WAIT
        WebDriverWait(self.driver, timeout).until(
            EC.url_contains(text)
        )

    def switch_to_frame(self, locator: tuple):
        """切换到 iframe"""
        frame = self.find_element(locator)
        self.driver.switch_to.frame(frame)
        log.debug(f"切换到 iframe: {locator}")

    def switch_to_default_content(self):
        """切回主文档"""
        self.driver.switch_to.default_content()

    # ==================== 截图 ====================

    def take_screenshot(self, name: str = None) -> str:
        """
        截图并保存
        :param name: 截图名称
        :return: 截图文件路径
        """
        name = name or f"screenshot_{int(time.time())}"
        file_path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
        self.driver.save_screenshot(file_path)
        log.info(f"截图已保存: {file_path}")
        return file_path

    # ==================== 下拉框 ====================

    def select_by_visible_text(self, locator: tuple, text: str):
        """通过可见文本选择下拉框选项"""
        from selenium.webdriver.support.select import Select
        element = self.find_element(locator)
        select = Select(element)
        select.select_by_visible_text(text)
        log.debug(f"选择下拉选项: {locator} -> '{text}'")

    # ==================== 窗口操作 ====================

    def switch_to_window(self, index: int = -1):
        """切换浏览器窗口"""
        handles = self.driver.window_handles
        self.driver.switch_to.window(handles[index])
        log.debug(f"切换到窗口索引: {index}")

    def close_current_window(self):
        """关闭当前窗口"""
        self.driver.close()
