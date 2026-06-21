"""
百度搜索项目级 conftest
提供项目特有的 fixtures 和配置
"""
import os

import pytest
import yaml

from core.logger import log


# ==================== 项目配置 fixture ====================

@pytest.fixture(scope="session")
def project_config():
    """加载项目配置文件"""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    log.info(f"加载项目配置: {config.get('project_name', 'unknown')}")
    return config


@pytest.fixture(scope="session")
def base_url(project_config):
    """获取项目基础 URL"""
    return project_config.get("base_url", "")
