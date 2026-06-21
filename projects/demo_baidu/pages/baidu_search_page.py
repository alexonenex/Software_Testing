"""
百度搜索页面对象
封装百度搜索页面的元素定位和操作
"""
from selenium.webdriver.common.by import By

from core.base_page import BasePage


class BaiduSearchPage(BasePage):
    """百度搜索页面"""

    # ==================== 元素定位器 ====================
    SEARCH_INPUT = (By.ID, "kw")
    SEARCH_BUTTON = (By.ID, "su")

    # ==================== 页面操作 ====================

    def open(self, base_url: str = "https://www.baidu.com"):
        """打开百度首页"""
        self.open_url(base_url)

    def search(self, keyword: str):
        """
        执行搜索操作
        :param keyword: 搜索关键词
        """
        self.input_text(self.SEARCH_INPUT, keyword)
        self.click(self.SEARCH_BUTTON)
        self.wait_for_url_contains("wd")

    def get_title(self) -> str:
        """获取页面标题"""
        return self.get_page_title()
