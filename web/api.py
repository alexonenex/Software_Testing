"""
API 路由
提供项目管理、测试运行、结果查询等 RESTful 接口
"""
import json
import os
import subprocess
import time
import uuid
import threading

import yaml
from flask import Blueprint, jsonify, request

api_bp = Blueprint("api", __name__)

# ==================== 运行状态存储 ====================
# 内存中保存运行状态（生产环境可换为 SQLite）
_test_runs = []


def _get_base_dir():
    """获取项目根目录"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_projects_dir():
    """获取项目目录"""
    return os.path.join(_get_base_dir(), "projects")


def _get_results_file():
    """获取结果存储文件"""
    path = os.path.join(_get_base_dir(), "reports", "test_history.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return []


def _save_results(data):
    """保存测试结果"""
    path = os.path.join(_get_base_dir(), "reports", "test_history.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==================== 项目 API ====================

@api_bp.route("/projects", methods=["GET"])
def list_projects():
    """获取所有项目列表"""
    projects_dir = _get_projects_dir()
    projects = []

    if os.path.exists(projects_dir):
        for name in sorted(os.listdir(projects_dir)):
            project_path = os.path.join(projects_dir, name)
            if os.path.isdir(project_path) and not name.startswith("_") and not name.startswith("."):
                config = {}
                config_path = os.path.join(project_path, "config.yaml")
                if os.path.exists(config_path):
                    try:
                        with open(config_path, "r", encoding="utf-8") as f:
                            config = yaml.safe_load(f) or {}
                    except Exception:
                        pass

                # 统计测试文件数量
                test_count = 0
                tests_dir = os.path.join(project_path, "tests")
                if os.path.exists(tests_dir):
                    for root, dirs, files in os.walk(tests_dir):
                        test_count += len([f for f in files if f.startswith("test_") and f.endswith(".py")])

                projects.append({
                    "id": name,
                    "name": config.get("project_name", name),
                    "description": config.get("project_desc", ""),
                    "test_count": test_count,
                    "browser": config.get("browser", "chrome"),
                    "priority": config.get("priority", ""),
                })

    return jsonify({"projects": projects, "total": len(projects)})


@api_bp.route("/projects", methods=["POST"])
def create_project():
    """创建新项目"""
    data = request.get_json()
    name = data.get("name", "").strip()
    if not name:
        return jsonify({"error": "项目名称不能为空"}), 400

    project_path = os.path.join(_get_projects_dir(), name)
    if os.path.exists(project_path):
        return jsonify({"error": f"项目 '{name}' 已存在"}), 409

    # 创建项目目录结构
    for subdir in ["tests", "pages", "data"]:
        os.makedirs(os.path.join(project_path, subdir), exist_ok=True)

    # 创建配置文件
    config = {
        "project_name": data.get("display_name", name),
        "project_desc": data.get("description", ""),
        "base_url": data.get("base_url", ""),
        "browser": data.get("browser", ""),
        "headless": False,
        "priority": data.get("priority", "p2"),
    }
    config_path = os.path.join(project_path, "config.yaml")
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)

    # 创建 __init__.py
    for subdir in ["", "tests", "pages"]:
        init_path = os.path.join(project_path, subdir, "__init__.py") if subdir else os.path.join(project_path, "__init__.py")
        with open(init_path, "w") as f:
            f.write("")

    return jsonify({"message": f"项目 '{name}' 创建成功", "project": config}), 201


@api_bp.route("/projects/<name>", methods=["DELETE"])
def delete_project(name):
    """删除项目"""
    project_path = os.path.join(_get_projects_dir(), name)
    if not os.path.exists(project_path):
        return jsonify({"error": f"项目 '{name}' 不存在"}), 404

    import shutil
    shutil.rmtree(project_path)
    return jsonify({"message": f"项目 '{name}' 已删除"})


# ==================== 测试运行 API ====================

@api_bp.route("/run", methods=["POST"])
def run_tests():
    """运行测试"""
    data = request.get_json() or {}
    project = data.get("project")  # 项目名称，为空则运行所有
    markers = data.get("markers", [])  # pytest markers
    extra_args = data.get("extra_args", "")  # 额外参数

    base_dir = _get_base_dir()
    run_id = str(uuid.uuid4())[:8]
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # 构建命令
    if project:
        project_path = os.path.join(_get_projects_dir(), project)
        if not os.path.exists(project_path):
            return jsonify({"error": f"项目 '{project}' 不存在"}), 404
        cmd = f'"{os.path.join(base_dir, "venv", "Scripts", "python.exe")}" -m pytest projects/{project}/tests/ -v --tb=short'
    else:
        cmd = f'"{os.path.join(base_dir, "venv", "Scripts", "python.exe")}" -m pytest projects/ -v --tb=short'

    # 添加 markers
    if markers:
        cmd += f" -m {' or '.join(markers)}"

    # 添加 JSON 报告输出
    report_file = os.path.join(base_dir, "reports", f"result_{run_id}.json")
    cmd += f' --json-report --json-report-file="{report_file}"'

    if extra_args:
        cmd += f" {extra_args}"

    # 记录运行信息
    run_info = {
        "id": run_id,
        "timestamp": timestamp,
        "project": project or "所有项目",
        "command": cmd,
        "status": "running",
        "output": "",
        "summary": None,
    }
    _test_runs.append(run_info)

    # 异步运行
    def _run_test():
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                cwd=base_dir,
                capture_output=True,
                text=True,
                timeout=300,
                encoding="utf-8",
            )
            run_info["output"] = result.stdout + result.stderr
            run_info["exit_code"] = result.returncode
            run_info["status"] = "passed" if result.returncode == 0 else "failed"

            # 解析 JSON 报告
            if os.path.exists(report_file):
                with open(report_file, "r", encoding="utf-8") as f:
                    report = json.load(f)
                    summary = report.get("summary", {})
                    run_info["summary"] = {
                        "total": summary.get("total", 0),
                        "passed": summary.get("passed", 0),
                        "failed": summary.get("failed", 0),
                        "error": summary.get("error", 0),
                        "skipped": summary.get("skipped", 0),
                        "duration": round(report.get("duration", 0), 2),
                    }
                    # 提取失败的测试详情
                    run_info["failures"] = []
                    for test in report.get("tests", []):
                        if test.get("outcome") == "failed":
                            run_info["failures"].append({
                                "name": test.get("nodeid", ""),
                                "message": test.get("call", {}).get("longrepr", ""),
                            })

            # 保存到历史
            history = _get_results_file()
            history.insert(0, run_info)
            if len(history) > 50:
                history = history[:50]
            _save_results(history)

        except subprocess.TimeoutExpired:
            run_info["status"] = "timeout"
            run_info["output"] = "测试运行超时（300秒）"
        except Exception as e:
            run_info["status"] = "error"
            run_info["output"] = str(e)

    thread = threading.Thread(target=_run_test)
    thread.start()

    return jsonify({"run_id": run_id, "status": "running", "message": "测试已启动"})


@api_bp.route("/run/<run_id>/status", methods=["GET"])
def get_run_status(run_id):
    """获取测试运行状态"""
    for run in _test_runs:
        if run["id"] == run_id:
            return jsonify(run)
    return jsonify({"error": "未找到该运行记录"}), 404


# ==================== 测试结果 API ====================

@api_bp.route("/results", methods=["GET"])
def get_results():
    """获取历史测试结果"""
    history = _get_results_file()
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    total = len(history)
    start = (page - 1) * per_page
    end = start + per_page

    return jsonify({
        "results": history[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
    })


@api_bp.route("/results/<run_id>", methods=["GET"])
def get_result_detail(run_id):
    """获取某次运行的详细信息"""
    history = _get_results_file()
    for run in history:
        if run["id"] == run_id:
            return jsonify(run)

    # 也查内存中的运行
    for run in _test_runs:
        if run["id"] == run_id:
            return jsonify(run)

    return jsonify({"error": "未找到该记录"}), 404


@api_bp.route("/dashboard", methods=["GET"])
def dashboard_stats():
    """仪表盘统计数据"""
    history = _get_results_file()
    projects_dir = _get_projects_dir()

    # 项目统计
    project_count = 0
    total_tests = 0
    if os.path.exists(projects_dir):
        for name in os.listdir(projects_dir):
            if os.path.isdir(os.path.join(projects_dir, name)) and not name.startswith(("_", ".")):
                project_count += 1

    # 最近一次运行的统计
    latest_run = history[0] if history else None

    # 通过率计算
    pass_rate = 0
    if latest_run and latest_run.get("summary"):
        s = latest_run["summary"]
        if s["total"] > 0:
            pass_rate = round(s["passed"] / s["total"] * 100, 1)

    # 总运行次数
    total_runs = len(history)
    passed_runs = len([r for r in history if r.get("status") == "passed"])

    return jsonify({
        "project_count": project_count,
        "total_runs": total_runs,
        "passed_runs": passed_runs,
        "pass_rate": pass_rate,
        "latest_run": latest_run,
    })
