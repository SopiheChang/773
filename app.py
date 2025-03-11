from flask import Flask, request, jsonify
import os
import requests

app = Flask(__name__)

# LINE Channel Access Token（必须在 LINE Developer 取得）
LINE_ACCESS_TOKEN = "e/tTdFZoZBNOYfiPmlnXkFnas2kRFHKE9Nc4/bAAT5gQVGbCw6fvj8vR0eOY6+tPLmdVBHhVHGm0+6jhbvojPOGZk9T1xBG++PQu2K9/5VktZOnkaasFzZ8mNh1D5mHDyp8b2hljWeZBvmszgRoFcwdB04t89/1O/w1cDnyilFU="
LINE_REPLY_URL = "https://api.line.me/v2/bot/message/reply"

@app.route("/")  # 主页
def home():
    return "Hello, this is my LINE Bot!"

@app.route("/webhook", methods=["POST"])  # 处理 LINE Webhook
def webhook():
    data = request.json
    print("Received webhook data:", data)  # 记录日志，方便调试
    
    # 确保 webhook 事件存在
    if "events" in data:
        for event in data["events"]:
            if event["type"] == "message" and event["message"]["type"] == "text":
                reply_token = event["replyToken"]  # 获取 Reply Token
                user_message = event["message"]["text"]  # 获取用户发送的消息
                reply_message = process_message(user_message)  # 处理消息
                send_reply(reply_token, reply_message)  # 发送回复
                
    return jsonify({"status": "ok"})  # 返回 JSON 响应，避免 LINE 重试请求

def process_message(user_message):
    """
    处理用户的消息，并返回 Bot 的回复
    """
    if user_message.isdigit():  # 如果是数字，计算天数
        return f"你输入的数字是 {user_message}，但还没有设定逻辑 😃"
    else:
        return f"你说了：{user_message}，Bot 收到了！🚀"

def send_reply(reply_token, reply_message):
    """
    发送回复给用户
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    payload = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": reply_message}]
    }
    response = requests.post(LINE_REPLY_URL, headers=headers, json=payload)
    print("LINE API Response:", response.json())  # 记录 LINE API 的返回信息

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
