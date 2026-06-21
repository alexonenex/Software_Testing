"""
全局配置文件
统一管理测试平台的所有配置项
"""
import os

# ==================== 项目路径 ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
SCREENSHOTS_DIR = os.path.join(BASE_DIR, "screenshots")
LOGS_DIR = os.path.join(BASE_DIR, "logs")

# 确保目录存在
for _dir in [REPORTS_DIR, SCREENSHOTS_DIR, LOGS_DIR]:
    os.makedirs(_dir, exist_ok=True)

# ==================== 运行环境 ====================
ENV = os.getenv("TEST_ENV", "test")  # test / staging / prod

# ==================== 超时设置（秒） ====================
IMPLICIT_WAIT = 10       # 隐式等待
PAGE_LOAD_TIMEOUT = 30   # 页面加载超时
SCRIPT_TIMEOUT = 30      # 脚本执行超时

# ==================== Web 测试配置 ====================
BROWSER = os.getenv("BROWSER", "chrome")  # chrome / firefox / edge
HEADLESS = os.getenv("HEADLESS", "false").lower() == "true"
WINDOW_SIZE = (1920, 1080)

# ==================== 重试配置 ====================
MAX_RETRIES = 2          # 失败重试次数
RETRY_DELAY = 1          # 重试间隔（秒）

# ==================== 日志配置 ====================
LOG_LEVEL = "DEBUG"
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} - {message}"
LOG_ROTATION = "10 MB"
LOG_RETENTION = "7 days"
