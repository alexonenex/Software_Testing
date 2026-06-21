"""
API 自动化测试示例
演示使用 requests 进行接口测试
"""
import allure
import pytest

from utils.logger import log


@allure.feature("API 测试")
@allure.story("JSONPlaceholder 接口")
class TestAPIDemo:
    """API 测试示例（使用 jsonplaceholder 免费 API）"""

    @allure.title("GET - 获取帖子列表")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_get_posts(self, api_session, api_base_url):
        """测试获取帖子列表接口"""
        log.info("开始执行获取帖子列表测试")

        response = api_session.get(f"{api_base_url}/posts", timeout=15)

        # 断言状态码
        assert response.status_code == 200, f"状态码应为200，实际为{response.status_code}"

        # 断言响应数据
        data = response.json()
        assert isinstance(data, list), "响应数据应为列表"
        assert len(data) > 0, "帖子列表不应为空"

        log.info(f"获取帖子列表成功，共 {len(data)} 条")

    @allure.title("GET - 获取单个帖子")
    @allure.severity(allure.severity_level.NORMAL)
    def test_get_single_post(self, api_session, api_base_url):
        """测试获取单个帖子接口"""
        response = api_session.get(f"{api_base_url}/posts/1", timeout=15)

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1, "帖子 ID 应为 1"
        assert "title" in data, "帖子应包含 title 字段"
        assert "body" in data, "帖子应包含 body 字段"

        log.info("获取单个帖子测试通过")

    @allure.title("POST - 创建帖子")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_create_post(self, api_session, api_base_url):
        """测试创建帖子接口"""
        payload = {
            "title": "自动化测试标题",
            "body": "这是一条由自动化测试创建的帖子",
            "userId": 1,
        }

        response = api_session.post(f"{api_base_url}/posts", json=payload, timeout=15)

        assert response.status_code == 201, f"创建帖子状态码应为201，实际为{response.status_code}"
        data = response.json()
        assert data["title"] == payload["title"], "返回标题应与请求一致"
        assert "id" in data, "返回数据应包含 id"

        log.info("创建帖子测试通过")

    @allure.title("PUT - 更新帖子")
    @allure.severity(allure.severity_level.NORMAL)
    def test_update_post(self, api_session, api_base_url):
        """测试更新帖子接口"""
        payload = {
            "id": 1,
            "title": "更新后的标题",
            "body": "更新后的内容",
            "userId": 1,
        }

        response = api_session.put(f"{api_base_url}/posts/1", json=payload, timeout=15)

        assert response.status_code == 200
        data = response.json()
        assert data["title"] == payload["title"], "更新后标题应一致"

        log.info("更新帖子测试通过")

    @allure.title("DELETE - 删除帖子")
    @allure.severity(allure.severity_level.NORMAL)
    def test_delete_post(self, api_session, api_base_url):
        """测试删除帖子接口"""
        response = api_session.delete(f"{api_base_url}/posts/1", timeout=15)

        assert response.status_code == 200, "删除帖子状态码应为200"

        log.info("删除帖子测试通过")
