"""
桌面应用页面基类
封装 pywinauto 的常用操作，实现桌面应用的 Page Object 模式
"""
import time

from utils.logger import log


class DesktopBasePage:
    """桌面应用页面基类，所有桌面页面类应继承此类"""

    def __init__(self, app):
        """
        :param app: pywinfo.Application 实例
        """
        self.app = app
        self.window = None

    def set_window(self, title: str = None, title_re: str = None, class_name: str = None):
        """
        设置当前操作的窗口
        :param title: 窗口精确标题
        :param title_re: 窗口标题正则匹配
        :param class_name: 窗口类名
        """
        kwargs = {}
        if title:
            kwargs["title"] = title
        if title_re:
            kwargs["title_re"] = title_re
        if class_name:
            kwargs["class_name"] = class_name

        self.window = self.app.window(**kwargs)
        self.window.wait("ready", timeout=15)
        log.info(f"已定位到窗口: {kwargs}")
        return self

    # ==================== 元素操作 ====================

    def find_by(self, **kwargs):
        """
        查找控件
        用法: find_by(title="确定", control_type="Button")
        """
        element = self.window.child_window(**kwargs)
        log.debug(f"查找控件: {kwargs}")
        return element

    def click_button(self, **kwargs):
        """点击按钮"""
        btn = self.find_by(**kwargs)
        btn.click()
        log.debug(f"点击按钮: {kwargs}")

    def input_text(self, text: str, **kwargs):
        """输入文本"""
        edit = self.find_by(**kwargs)
        edit.set_text(text)
        log.debug(f"输入文本: {kwargs} -> '{text}'")

    def get_text(self, **kwargs) -> str:
        """获取控件文本"""
        element = self.find_by(**kwargs)
        return element.window_text()

    # ==================== 窗口操作 ====================

    def maximize(self):
        """最大化窗口"""
        self.window.maximize()
        log.debug("窗口已最大化")

    def minimize(self):
        """最小化窗口"""
        self.window.minimize()
        log.debug("窗口已最小化")

    def restore(self):
        """还原窗口"""
        self.window.restore()
        log.debug("窗口已还原")

    def close(self):
        """关闭窗口"""
        self.window.close()
        log.debug("窗口已关闭")

    def take_screenshot(self, name: str = None):
        """截图（pywinauto）"""
        import os
        from config.settings import SCREENSHOTS_DIR
        name = name or f"desktop_{int(time.time())}"
        file_path = os.path.join(SCREENSHOTS_DIR, f"{name}.png")
        try:
            self.window.capture_as_image().save(file_path)
            log.info(f"桌面截图已保存: {file_path}")
        except Exception as e:
            log.warning(f"桌面截图失败: {e}")

    def wait_for_idle(self, timeout: int = 10):
        """等待窗口空闲"""
        self.window.wait("ready", timeout=timeout)
        log.debug("窗口就绪")
