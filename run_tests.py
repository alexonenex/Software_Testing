"""
测试运行入口脚本
提供多种运行模式，方便通过命令行执行
"""
import subprocess
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_all():
    """运行所有测试"""
    cmd = "pytest tests/ -v --alluredir=reports/allure-results"
    _run(cmd)


def run_web():
    """仅运行 Web UI 测试"""
    cmd = "pytest tests/test_web_demo.py -v -m web --alluredir=reports/allure-results"
    _run(cmd)


def run_api():
    """仅运行 API 测试"""
    cmd = "pytest tests/test_api_demo.py -v -m api --alluredir=reports/allure-results"
    _run(cmd)


def run_desktop():
    """仅运行桌面应用测试"""
    cmd = "pytest tests/test_desktop_demo.py -v -m desktop --alluredir=reports/allure-results"
    _run(cmd)


def run_smoke():
    """运行冒烟测试"""
    cmd = "pytest tests/ -v -m smoke --alluredir=reports/allure-results"
    _run(cmd)


def run_parallel():
    """并行运行所有测试（4个进程）"""
    cmd = "pytest tests/ -v -n 4 --alluredir=reports/allure-results"
    _run(cmd)


def generate_report():
    """生成 Allure 测试报告"""
    cmd = "allure generate reports/allure-results -o reports/allure-report --clean"
    _run(cmd)


def open_report():
    """打开 Allure 测试报告"""
    cmd = "allure open reports/allure-report"
    _run(cmd)


def _run(cmd: str):
    """执行命令"""
    print(f"\n{'='*60}")
    print(f"执行命令: {cmd}")
    print(f"{'='*60}\n")
    result = subprocess.run(cmd, shell=True, cwd=os.path.dirname(os.path.abspath(__file__)))
    sys.exit(result.returncode)


if __name__ == "__main__":
    # 用法: python run_tests.py [模式]
    modes = {
        "all": run_all,
        "web": run_web,
        "api": run_api,
        "desktop": run_desktop,
        "smoke": run_smoke,
        "parallel": run_parallel,
        "report": generate_report,
        "open": open_report,
    }

    if len(sys.argv) < 2:
        print("用法: python run_tests.py <模式>")
        print(f"可用模式: {', '.join(modes.keys())}")
        sys.exit(1)

    mode = sys.argv[1]
    if mode in modes:
        modes[mode]()
    else:
        print(f"未知模式: {mode}")
        print(f"可用模式: {', '.join(modes.keys())}")
        sys.exit(1)