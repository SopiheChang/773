from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route("/")  # 主页
def home():
    return "Hello, this is my LINE Bot!"

@app.route("/webhook", methods=["POST"])  # 处理 LINE Webhook
def webhook():
    data = request.json
    print("Received webhook data:", data)  # 先打印收到的数据，方便调试
    return jsonify({"status": "ok"})  # 返回 JSON 响应，避免 LINE 重试请求

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
