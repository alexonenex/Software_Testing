"""
日志工具模块
基于 loguru 实现统一的日志管理
"""
import sys
from loguru import logger

from config.settings import LOGS_DIR, LOG_LEVEL, LOG_FORMAT, LOG_ROTATION, LOG_RETENTION


def setup_logger():
    """
    配置全局日志器
    - 控制台输出：DEBUG 级别，带颜色
    - 文件输出：INFO 级别，按大小轮转
    """
    # 移除 loguru 默认 handler
    logger.remove()

    # 控制台输出
    logger.add(
        sys.stderr,
        level=LOG_LEVEL,
        format="<green>{time:HH:mm:ss}</green> | <level>{level:<8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
        colorize=True,
    )

    # 全量日志文件
    logger.add(
        os_path_join(LOGS_DIR, "test_{time:YYYY-MM-DD}.log"),
        level="DEBUG",
        format=LOG_FORMAT,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        encoding="utf-8",
        enqueue=True,
    )

    # 错误日志单独文件
    logger.add(
        os_path_join(LOGS_DIR, "error_{time:YYYY-MM-DD}.log"),
        level="ERROR",
        format=LOG_FORMAT,
        rotation=LOG_ROTATION,
        retention=LOG_RETENTION,
        encoding="utf-8",
        enqueue=True,
    )

    return logger


def os_path_join(*paths):
    """兼容路径拼接"""
    import os
    return os.path.join(*paths)


# 初始化全局日志器
log = setup_logger()
