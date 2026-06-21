"""
多项目测试运行入口脚本
支持按项目运行、运行全部、并行运行等多种模式

用法:
    python run_tests.py                          # 显示用法
    python run_tests.py all                      # 运行所有项目的测试
    python run_tests.py demo_baidu               # 运行指定项目的测试
    python run_tests.py demo_baidu -m smoke      # 运行指定项目的冒烟测试
    python run_tests.py parallel                 # 并行运行所有测试
    python run_tests.py list                     # 列出所有可用项目
    python run_tests.py report                   # 生成 Allure 测试报告
    python run_tests.py open                     # 打开 Allure 测试报告
"""
import subprocess
import sys
import os

# 确保项目根目录在 Python 路径中
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECTS_DIR = os.path.join(BASE_DIR, "projects")


def get_projects():
    """获取所有可用项目列表"""
    if not os.path.exists(PROJECTS_DIR):
        return []
    projects = []
    for name in os.listdir(PROJECTS_DIR):
        project_path = os.path.join(PROJECTS_DIR, name)
        if os.path.isdir(project_path) and not name.startswith("_") and not name.startswith("."):
            projects.append(name)
    return sorted(projects)


def run_all():
    """运行所有项目的测试"""
    cmd = "pytest projects/ -v --alluredir=reports/allure-results"
    _run(cmd)


def run_project(project_name: str, extra_args: str = ""):
    """
    运行指定项目的测试
    :param project_name: 项目名称
    :param extra_args: 额外的 pytest 参数（如 -m smoke）
    """
    project_path = os.path.join(PROJECTS_DIR, project_name)
    if not os.path.exists(project_path):
        print(f"错误: 项目 '{project_name}' 不存在")
        print(f"可用项目: {', '.join(get_projects())}")
        sys.exit(1)
    cmd = f"pytest projects/{project_name}/ -v --alluredir=reports/allure-results"
    if extra_args:
        cmd += f" {extra_args}"
    _run(cmd)


def run_parallel():
    """并行运行所有测试（4个进程）"""
    cmd = "pytest projects/ -v -n 4 --alluredir=reports/allure-results"
    _run(cmd)


def list_projects():
    """列出所有可用项目"""
    projects = get_projects()
    print(f"\n{'='*60}")
    print(f"可用项目 ({len(projects)} 个):")
    print(f"{'='*60}")
    for p in projects:
        config_path = os.path.join(PROJECTS_DIR, p, "config.yaml")
        desc = ""
        if os.path.exists(config_path):
            try:
                import yaml
                with open(config_path, "r", encoding="utf-8") as f:
                    config = yaml.safe_load(f)
                    desc = config.get("project_name", "")
            except Exception:
                pass
        print(f"  - {p}" + (f"  ({desc})" if desc else ""))
    print(f"\n用法: python run_tests.py <项目名>")
    print(f"{'='*60}\n")


def generate_report():
    """生成 Allure 测试报告"""
    cmd = "allure generate reports/allure-results -o reports/allure-report --clean"
    _run(cmd)


def open_report():
    """打开 Allure 测试报告"""
    cmd = "allure open reports/allure-report"
    _run(cmd)


def start_web():
    """启动 Web 管理界面"""
    import subprocess as sp
    python_exe = os.path.join(BASE_DIR, "venv", "Scripts", "python.exe")
    if not os.path.exists(python_exe):
        python_exe = sys.executable
    print("\n" + "=" * 50)
    print("  启动 Web 管理界面...")
    print("  访问地址: http://localhost:5000")
    print("  按 Ctrl+C 停止")
    print("=" * 50 + "\n")
    sp.run([python_exe, "-m", "web.app"], cwd=BASE_DIR)


def _run(cmd: str):
    """执行命令"""
    print(f"\n{'='*60}")
    print(f"执行命令: {cmd}")
    print(f"{'='*60}\n")
    result = subprocess.run(cmd, shell=True, cwd=BASE_DIR)
    sys.exit(result.returncode)


if __name__ == "__main__":
    modes = {
        "all": run_all,
        "parallel": run_parallel,
        "list": list_projects,
        "report": generate_report,
        "open": open_report,
        "web": start_web,
    }

    if len(sys.argv) < 2:
        print("用法: python run_tests.py <模式|项目名> [额外参数]")
        print(f"\n内置模式: {', '.join(modes.keys())}")
        print(f"可用项目: {', '.join(get_projects())}")
        print("\n示例:")
        print("  python run_tests.py all                  # 运行所有项目测试")
        print("  python run_tests.py demo_baidu           # 运行指定项目测试")
        print("  python run_tests.py demo_baidu -m smoke  # 运行指定项目冒烟测试")
        print("  python run_tests.py list                 # 列出所有项目")
        print("  python run_tests.py web                  # 启动 Web 管理界面")
        sys.exit(1)

    mode = sys.argv[1]
    extra_args = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""

    if mode in modes:
        modes[mode]()
    elif mode not in modes:
        # 尝试作为项目名处理
        projects = get_projects()
        if mode in projects:
            run_project(mode, extra_args)
        else:
            print(f"未知模式或项目: {mode}")
            print(f"内置模式: {', '.join(modes.keys())}")
            print(f"可用项目: {', '.join(projects)}")
            sys.exit(1)
