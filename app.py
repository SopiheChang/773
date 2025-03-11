import os
import datetime
import pandas as pd
import requests
from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_FILE_URL = "https://raw.githubusercontent.com/SopiheChang/773/main/data.xlsx"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

PRESET_DAYS = [27, 38, 45, 56, 69, 76, 95, 112, 120, 130, 140, 150, 156, 167]

def download_excel():
    """从 GitHub 下载最新的 Excel 文件"""
    response = requests.get(GITHUB_FILE_URL)
    with open("data.xlsx", "wb") as file:
        file.write(response.content)

def read_excel_data():
    """读取 Excel 并转换为字典格式"""
    df = pd.read_excel("data.xlsx", header=0)
    data = {}
    for col in df.columns[1:]:  # 跳过第一列（名称列）
        data[col] = df[[df.columns[0], col]].dropna().to_dict(orient='records')
    return data

def find_nearest_days(day_diff):
    return max([d for d in PRESET_DAYS if d <= day_diff], default=PRESET_DAYS[0])

@app.route("/", methods=["GET"])
def home():
    return "Hello, this is my LINE Bot!"

@app.route("/webhook", methods=["POST"])
def webhook():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400
    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_input = event.message.text.strip()
    try:
        input_date = datetime.datetime.strptime(user_input, "%Y%m%d").date()
        today = datetime.date.today()
        day_diff = (today - input_date).days
        nearest_days = find_nearest_days(day_diff)
        
        download_excel()
        excel_data = read_excel_data()
        extra_text = "\n".join([f"{row[df.columns[0]]}: {row[nearest_days]}" for row in excel_data.get(nearest_days, [])])
        
        flex_message = generate_flex_message(user_input, day_diff, nearest_days, extra_text)
        line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="計算結果", contents=flex_message))
    except ValueError:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 請輸入正確的日期格式（YYYYMMDD）"))

def generate_flex_message(user_date, day_diff, nearest_days, extra_text):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "📅 您輸入的日期：", "weight": "bold", "size": "md"},
                {"type": "text", "text": f"{user_date}", "size": "lg", "color": "#00bfff"},
                {"type": "separator"},
                {"type": "text", "text": f"⏳ 距今 {day_diff} 天", "size": "md"},
                {"type": "text", "text": f"🎯 對應：{nearest_days} 天", "weight": "bold", "size": "lg", "color": "#ff5555"},
                {"type": "separator"},
                {"type": "text", "text": extra_text if extra_text else "🔍 无额外说明", "size": "md", "wrap": True, "color": "#008000"}
            ]
        }
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
