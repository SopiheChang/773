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

def process_message(user_input):
    """处理用户输入的日期，计算天数并返回 Flex Message"""
    try:
        # 解析用户输入的日期
        input_date = datetime.datetime.strptime(user_input, "%Y%m%d").date()
        today = datetime.date.today()
        day_diff = (today - input_date).days  # 计算天数差

        # 找到最近的天数匹配
        nearest_days = find_nearest_days(day_diff)

        # 📌 这里是 Flex Message 的 JSON，你可以用 Flex Simulator 调整后替换！
        flex_message = {
            "type": "flex",
            "altText": f"计算结果：{day_diff} 天，匹配 {nearest_days} 天",
            "contents": {
                "type": "bubble",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        {"type": "text", "text": f"📅 你输入的日期：{user_input}", "weight": "bold", "size": "lg"},
                        {"type": "text", "text": f"⏳ 距今 {day_diff} 天", "size": "md"},
                        {"type": "text", "text": f"🎯 匹配值：{nearest_days} 天", "weight": "bold", "size": "lg", "color": "#ff5555"},
                        {"type": "text", "text": "👇 点击下方按钮查看更多详情", "size": "sm", "color": "#aaaaaa"}
                    ]
                },
                "footer": {
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {
                            "type": "button",
                            "style": "primary",
                            "color": "#1DB446",
                            "action": {
                                "type": "uri",
                                "label": "查看详情",
                                "uri": "https://your-website.com/details"
                            }
                        }
                    ]
                }
            }
        }
        return flex_message

    except ValueError:
        return {"type": "text", "text": "❌ 请输入正确的日期格式（YYYYMMDD）"}

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
