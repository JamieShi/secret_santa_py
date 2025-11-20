# app.py
from flask import Flask, request, jsonify
import random

# 创建 Flask 应用
# static_folder="static"：指定静态文件目录
# static_url_path=""：让 http://localhost:5000/ 直接访问 static/index.html
app = Flask(__name__, static_folder="static", static_url_path="")

# 固定的参与者名单
participant_names = ["Jamie", "Emily", "Xiwei", "Yujia", "Ruolan"]

# participants 记录每个人是否已经抽签
participants = [{"name": name, "hasDrawn": False} for name in participant_names]

# secret_mapping 用来保存隐藏的 Secret Santa 对应关系
# 例如：{"Jamie": "Yujia", "Emily": "Jamie", ...}
secret_mapping = None


# ========== 工具函数：生成无固定点排列（derangement） ==========

def shuffle_list(items):
    """简单封装一下随机打乱"""
    items = list(items)
    random.shuffle(items)
    return items


def generate_derangement(items):
    """
    生成一个无固定点排列：
    对于每个 i，都有 shuffled[i] != items[i]
    """
    items = list(items)
    n = len(items)
    while True:
        shuffled = shuffle_list(items)
        # 检查是否每个位置都不等于原来的元素
        if all(shuffled[i] != items[i] for i in range(n)):
            mapping = {items[i]: shuffled[i] for i in range(n)}
            return mapping


def ensure_mapping_initialized():
    """如果还没有生成配对表，就生成一次"""
    global secret_mapping
    if secret_mapping is None:
        secret_mapping = generate_derangement(participant_names)
        print("Secret mapping generated:", secret_mapping)


# ========== 路由 ==========

@app.route("/")
def index():
    """返回前端页面（static/index.html）"""
    return app.send_static_file("index.html")


@app.get("/api/state")
def get_state():
    """获取当前抽签状态（只返回谁抽过了）"""
    ensure_mapping_initialized()
    return jsonify({"participants": participants})


@app.post("/api/draw")
def draw():
    """
    进行抽签：
    前端发送 JSON: {"name": "Jamie"}
    返回: {"recipient": "xxx"} 或错误信息
    """
    data = request.get_json(silent=True) or {}
    name = data.get("name")

    if not name or name not in participant_names:
        return jsonify({"error": "无效的名字"}), 400

    ensure_mapping_initialized()

    # 找到对应的参与者记录
    participant = next((p for p in participants if p["name"] == name), None)
    if participant is None:
        return jsonify({"error": "找不到该参与者"}), 400

    if participant["hasDrawn"]:
        return jsonify({"error": "你已经抽过了，不能重复抽签"}), 400

    recipient = secret_mapping.get(name)
    if not recipient:
        return jsonify({"error": "内部错误：未找到抽签结果"}), 500

    # 标记为已抽签
    participant["hasDrawn"] = True

    return jsonify({"recipient": recipient})


@app.post("/api/reset")
def reset():
    """
    可选：重置接口（只给你自己调试用）
    调用后所有人变为未抽签，重新生成配对表
    """
    global participants, secret_mapping
    participants = [{"name": name, "hasDrawn": False} for name in participant_names]
    secret_mapping = None
    return jsonify({"message": "已重置 Secret Santa 状态"})


if __name__ == "__main__":
    from flask import Flask
    app.run(host="0.0.0.0", port=5000)