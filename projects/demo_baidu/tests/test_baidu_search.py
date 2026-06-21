"""
百度搜索 UI 自动化测试
"""
import os

import allure
import pytest
import yaml

from projects.demo_baidu.pages.baidu_search_page import BaiduSearchPage
from core.logger import log


def load_test_data():
    """加载测试数据"""
    data_path = os.path.join(os.path.dirname(__file__), "..", "data", "test_data.yaml")
    with open(data_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@allure.feature("百度搜索")
@allure.story("搜索功能")
class TestBaiduSearch:
    """百度搜索功能测试"""

    @pytest.fixture(autouse=True)
    def setup(self, web_driver, web_screenshot_on_failure, base_url):
        """每个测试方法前初始化页面"""
        self.page = BaiduSearchPage(web_driver)
        self.page.open(base_url)

    @allure.title("百度搜索 - 关键词搜索")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_search(self):
        """测试百度搜索功能"""
        log.info("开始执行百度搜索测试")

        self.page.search("自动化测试")

        title = self.page.get_title()
        assert "百度" in title, f"搜索后页面标题应包含'百度'，实际为: {title}"

        log.info("百度搜索测试通过")

    @allure.title("百度搜索 - 页面标题验证")
    @allure.severity(allure.severity_level.NORMAL)
    def test_page_title(self, base_url):
        """测试百度首页标题"""
        title = self.page.get_title()
        assert "百度" in title, f"页面标题应包含'百度'，实际为: {title}"

    @allure.title("百度搜索 - 数据驱动搜索")
    @allure.severity(allure.severity_level.NORMAL)
    @pytest.mark.parametrize("keyword", load_test_data()["search_keywords"])
    def test_search_with_data(self, keyword):
        """数据驱动：使用多组关键词搜索"""
        log.info(f"数据驱动搜索，关键词: {keyword}")

        self.page.search(keyword)

        title = self.page.get_title()
        assert "百度" in title, f"搜索'{keyword}'后标题应包含'百度'，实际为: {title}"
