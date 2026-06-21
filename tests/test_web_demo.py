"""
Web UI 自动化测试示例
演示使用 POM 模式进行 Web 页面测试
"""
import allure
import pytest

from pages.base_page import BasePage
from utils.logger import log


@allure.feature("Web UI 测试")
@allure.story("百度搜索")
class TestBaiduSearch:
    """百度搜索功能测试示例"""

    @pytest.fixture(autouse=True)
    def setup(self, web_driver, web_screenshot_on_failure):
        """每个测试方法前初始化页面"""
        self.page = BasePage(web_driver)
        self.page.open_url("https://www.baidu.com")

    @allure.title("百度搜索 - 关键词搜索")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_search(self):
        """测试百度搜索功能"""
        from selenium.webdriver.common.by import By

        log.info("开始执行百度搜索测试")

        # 输入搜索关键词
        search_input = (By.ID, "kw")
        self.page.input_text(search_input, "自动化测试")

        # 点击搜索按钮
        search_button = (By.ID, "su")
        self.page.click(search_button)

        # 验证搜索结果页面
        self.page.wait_for_url_contains("wd")
        assert "百度" in self.page.get_page_title(), "搜索后页面标题应包含'百度'"

        log.info("百度搜索测试通过")

    @allure.title("百度搜索 - 页面标题验证")
    @allure.severity(allure.severity_level.NORMAL)
    def test_page_title(self):
        """测试百度首页标题"""
        title = self.page.get_page_title()
        assert "百度" in title, f"页面标题应包含'百度'，实际为: {title}"
