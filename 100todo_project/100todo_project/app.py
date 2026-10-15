from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import os

app = Flask(__name__)
CORS(app)
DB_NAME = "todo.db"

# 初始化数据库
def init_db():
    conn = sqlite3.connect(DB_NAME)
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

# 访问首页，读取static里面的index.html
@app.route('/')
def index():
    return send_from_directory("static", "index.html")

# 获取用户已完成任务接口
@app.route("/api/get/<sid>")
def get_todo(sid):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    rows = cur.execute("SELECT item_index FROM user_todo WHERE session_id = ?", (sid,)).fetchall()
    conn.close()
    done_list = [row[0] for row in rows]
    return jsonify(done_list)

# 保存勾选状态接口
@app.route("/api/save", methods=["POST"])
def save_todo():
    data = request.get_json()
    sid = data.get("sid")
    doneList = data.get("doneList", [])

    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # 先删除旧记录
    cur.execute("DELETE FROM user_todo WHERE session_id = ?", (sid,))
    # 插入新的勾选记录
    for idx in doneList:
        cur.execute("INSERT INTO user_todo(session_id, item_index) VALUES (?,?)", (sid, idx))
    conn.commit()
    conn.close()
    return jsonify({"ok": True})

if __name__ == '__main__':
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)
