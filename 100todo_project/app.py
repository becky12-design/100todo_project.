from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "todo.db")
STATIC_DIR = os.path.join(BASE_DIR, "static")

app = Flask(__name__)
CORS(app)


# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''
    CREATE TABLE IF NOT EXISTS user_todo (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        item_index INTEGER
    )
    ''')
    conn.commit()
    conn.close()


# 关键修复：模块被导入时立刻建表。
# gunicorn 是用 import 的方式加载 app 的，不会执行下面的 __main__ 分支，
# 所以原来写在 __main__ 里的 init_db() 在线上从来没执行过。
init_db()


# 访问首页，读取static里面的index.html
@app.route('/')
def index():
    return send_from_directory(STATIC_DIR, "index.html")


# 健康检查（方便确认服务是否活着）
@app.route("/api/health")
def health():
    return jsonify({"ok": True})


# 获取用户已完成任务接口
@app.route("/api/get/<sid>")
def get_todo(sid):
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT item_index FROM user_todo WHERE session_id = ?", (sid,)
        ).fetchall()
    finally:
        conn.close()
    done_list = [row[0] for row in rows]
    return jsonify(done_list)


# 保存勾选状态接口
@app.route("/api/save", methods=["POST"])
def save_todo():
    data = request.get_json(silent=True) or {}
    sid = data.get("sid")
    doneList = data.get("doneList", [])

    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        # 先删除旧记录
        cur.execute("DELETE FROM user_todo WHERE session_id = ?", (sid,))
        # 插入新的勾选记录
        for idx in doneList:
            cur.execute("INSERT INTO user_todo(session_id, item_index) VALUES (?,?)", (sid, idx))
        conn.commit()
    finally:
        conn.close()
    return jsonify({"ok": True})


if __name__ == '__main__':
    # 本地：默认 5000 端口 + 调试模式；线上（Render 会注入 PORT）：跟随 PORT，关闭调试
    port = int(os.environ.get("PORT", 5000))
    is_local = os.environ.get("PORT") is None
    app.run(host="0.0.0.0", port=port, debug=is_local)