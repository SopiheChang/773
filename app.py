from flask import Flask, request, jsonify
import requests
import os


app = Flask(__name__)

# 你的 LINE Bot Channel Access Token
LINE_ACCESS_TOKEN = "你的_CHANNEL_ACCESS_TOKEN"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json()
    if "events" in data:
        for event in data["events"]:
            if event["type"] == "message" and event["message"]["type"] == "text":
                reply_token = event["replyToken"]
                user_message = event["message"]["text"]
                
                # 简单回传用户输入的内容
                reply_to_line(reply_token, f"你输入了: {user_message}")

    return "OK"

def reply_to_line(reply_token, message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_ACCESS_TOKEN}"
    }
    body = {
        "replyToken": reply_token,
        "messages": [{"type": "text", "text": message}]
    }
    requests.post("https://api.line.me/v2/bot/message/reply", headers=headers, json=body)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # 让 Render 使用它提供的 PORT
    app.run(host="0.0.0.0", port=port, debug=True)
