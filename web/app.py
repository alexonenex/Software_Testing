"""
Flask Web 管理界面
提供测试平台的 Web 管理后台
"""
import os
import sys

# 确保项目根目录在 Python 路径中
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from flask import Flask, render_template, send_from_directory
from flask_cors import CORS
from web.api import api_bp


def create_app():
    """创建 Flask 应用"""
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(__file__), "templates"),
        static_folder=os.path.join(os.path.dirname(__file__), "static"),
    )

    CORS(app)
    app.config["SECRET_KEY"] = "software-testing-platform"
    app.config["BASE_DIR"] = BASE_DIR

    # 注册 API 蓝图
    app.register_blueprint(api_bp, url_prefix="/api")

    # 前端页面路由
    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/<path:filename>")
    def static_files(filename):
        return send_from_directory(app.static_folder, filename)

    return app


if __name__ == "__main__":
    app = create_app()
    print("\n" + "=" * 50)
    print("  测试平台管理后台已启动")
    print("  访问地址: http://localhost:5000")
    print("=" * 50 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)
