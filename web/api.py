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

    # 异步运行（使用 Popen 流式输出）
    def _run_test():
        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                cwd=base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            # 实时读取输出
            output_lines = []
            start_time = time.time()
            for line in proc.stdout:
                output_lines.append(line)
                run_info["output"] = "".join(output_lines[-500:])  # 保留最近500行
                # 超时检查
                if time.time() - start_time > 300:
                    proc.kill()
                    output_lines.append("\n测试运行超时（300秒）\n")
                    run_info["status"] = "timeout"
                    break

            proc.wait()
            run_info["output"] = "".join(output_lines[-500:])
            if run_info["status"] == "running":
                run_info["exit_code"] = proc.returncode
                run_info["status"] = "passed" if proc.returncode == 0 else "failed"

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
    """获取历史测试结果（支持筛选）"""
    history = _get_results_file()

    # 筛选条件
    project_filter = request.args.get("project", "")
    status_filter = request.args.get("status", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")

    # 应用筛选
    filtered = history
    if project_filter:
        filtered = [r for r in filtered if r.get("project") == project_filter]
    if status_filter:
        filtered = [r for r in filtered if r.get("status") == status_filter]
    if date_from:
        filtered = [r for r in filtered if r.get("timestamp", "") >= date_from]
    if date_to:
        filtered = [r for r in filtered if r.get("timestamp", "") <= date_to + " 23:59:59"]

    # 分页
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    total = len(filtered)
    start = (page - 1) * per_page
    end = start + per_page

    # 获取所有项目名（用于筛选下拉）
    all_projects = list(set(r.get("project", "") for r in history if r.get("project")))

    return jsonify({
        "results": filtered[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
        "projects": sorted(all_projects),
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


@api_bp.route("/results/<run_id>/report", methods=["GET"])
def generate_report(run_id):
    """为某次运行生成 HTML 测试报告"""
    from flask import Response

    # 查找运行记录
    run = None
    history = _get_results_file()
    for r in history:
        if r["id"] == run_id:
            run = r
            break
    if not run:
        for r in _test_runs:
            if r["id"] == run_id:
                run = r
                break
    if not run:
        return jsonify({"error": "未找到该记录"}), 404

    s = run.get("summary", {}) or {}
    failures = run.get("failures", [])

    # 生成 HTML 报告
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>测试报告 - {run.get('project', '')}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; padding: 40px; color: #333; }}
        .container {{ max-width: 900px; margin: 0 auto; }}
        h1 {{ font-size: 24px; margin-bottom: 8px; }}
        .meta {{ color: #666; font-size: 14px; margin-bottom: 24px; }}
        .summary {{ display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; margin-bottom: 32px; }}
        .summary-item {{ background: white; border-radius: 8px; padding: 16px; text-align: center; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .summary-item .num {{ font-size: 28px; font-weight: 700; }}
        .summary-item .label {{ font-size: 12px; color: #666; margin-top: 4px; }}
        .green {{ color: #22c55e; }}
        .red {{ color: #ef4444; }}
        .blue {{ color: #3b82f6; }}
        .gray {{ color: #9ca3af; }}
        .section {{ background: white; border-radius: 8px; padding: 20px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        .section h2 {{ font-size: 16px; margin-bottom: 12px; }}
        .output {{ background: #1a1d27; color: #a1a1aa; padding: 16px; border-radius: 8px; font-family: monospace; font-size: 13px; white-space: pre-wrap; max-height: 400px; overflow-y: auto; }}
        .fail-item {{ border-left: 3px solid #ef4444; padding: 12px; margin-bottom: 8px; background: #fef2f2; }}
        .fail-item .name {{ font-weight: 600; margin-bottom: 4px; }}
        .fail-item .msg {{ font-size: 13px; color: #666; font-family: monospace; }}
        .status-badge {{ display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 12px; font-weight: 500; }}
        .status-passed {{ background: #dcfce7; color: #16a34a; }}
        .status-failed {{ background: #fef2f2; color: #dc2626; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>测试报告</h1>
        <p class="meta">
            项目: <strong>{run.get('project', '')}</strong> |
            时间: {run.get('timestamp', '')} |
            状态: <span class="status-badge status-{run.get('status', '')}">{run.get('status', '')}</span>
        </p>

        <div class="summary">
            <div class="summary-item"><div class="num blue">{s.get('total', 0)}</div><div class="label">总计</div></div>
            <div class="summary-item"><div class="num green">{s.get('passed', 0)}</div><div class="label">通过</div></div>
            <div class="summary-item"><div class="num red">{s.get('failed', 0)}</div><div class="label">失败</div></div>
            <div class="summary-item"><div class="num red">{s.get('error', 0)}</div><div class="label">错误</div></div>
            <div class="summary-item"><div class="num gray">{s.get('skipped', 0)}</div><div class="label">跳过</div></div>
        </div>

        <div class="section">
            <h2>通过率: {round(s.get('passed', 0) / max(s.get('total', 1), 1) * 100, 1)}% | 耗时: {s.get('duration', 0)}s</h2>
        </div>
"""
    # 失败详情
    if failures:
        html += '        <div class="section"><h2>失败详情</h2>\n'
        for f in failures:
            html += f'            <div class="fail-item"><div class="name">{f.get("name", "")}</div><div class="msg">{f.get("message", "")[:500]}</div></div>\n'
        html += '        </div>\n'

    # 完整输出
    html += f"""
        <div class="section">
            <h2>完整运行日志</h2>
            <div class="output">{run.get('output', '无输出')}</div>
        </div>

        <div class="section">
            <h2>执行命令</h2>
            <div class="output">{run.get('command', '')}</div>
        </div>
    </div>
</body>
</html>"""

    return Response(html, mimetype="text/html", headers={
        "Content-Disposition": f"inline; filename=report_{run_id}.html"
    })


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
