from flask import Flask, request
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, FlexSendMessage, TextSendMessage
import os
import datetime
import requests
import pandas as pd

app = Flask(__name__)

LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_FILE_URL = "https://raw.githubusercontent.com/SopiheChang/773/main/data.xlsx"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

PRESET_DAYS = [27, 38, 45, 56, 69, 76, 95, 112, 120, 130, 140, 150, 156, 167]

def download_excel():
    response = requests.get(GITHUB_FILE_URL)
    with open("data.xlsx", "wb") as file:
        file.write(response.content)

def get_excel_data(nearest_days):
    download_excel()
    df = pd.read_excel("data.xlsx")
    
    if nearest_days not in df.columns:
        return "🔍 無額外說明"
    
    data = []
    for i in range(3, 29):  # 第4~29行
        name = df.iloc[i, 1]  # B列名稱
        value = df.iloc[i, df.columns.get_loc(nearest_days)]  # 對應天數的值
        if pd.notna(value):
            data.append(f"{name}: {value}")
    
    return "\n".join(data) if data else "🔍 無額外說明"

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
    """處理收到的文本消息"""
    user_input = event.message.text.strip()

    try:
        # 解析日期並計算天數差
        input_date = datetime.datetime.strptime(user_input, "%Y%m%d").date()
        today = datetime.date.today()
        day_diff = (today - input_date).days

        # 找到最接近的預設數值
        nearest_days = find_nearest_days(day_diff)

        # 從 Excel 獲取數據
        extra_text = get_excel_data(nearest_days)

        # 生成 Flex Message
        flex_message = generate_flex_message(user_input, day_diff, nearest_days, extra_text)

        # **新增可複製的文字**
        text_message = TextSendMessage(text=f"📅 日期: {user_input}\n"
                                            f"⏳ 距今: {day_diff} 天\n"
                                            f"🎯 對應: {nearest_days} 天\n"
                                            f"{extra_text}")

        # **同時發送 Flex Message + 可複製的文字**
        line_bot_api.reply_message(event.reply_token, [flex_message, text_message])

    except ValueError:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 請輸入正確的日期格式（YYYYMMDD）"))

def generate_flex_message(user_date, day_diff, nearest_days, extra_text):
    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "📅 您輸入的離乳日期：", "weight": "bold", "size": "md"},
                {"type": "text", "text": f"{user_date}", "size": "lg", "color": "#00bfff"},
                {"type": "separator"},
                {"type": "text", "text": f"⏳ 日齡 {day_diff} 天", "size": "md"},
                {"type": "text", "text": f"🎯 對應：{nearest_days} 天", "weight": "bold", "size": "lg", "color": "#ff5555"},
                {"type": "separator"},
                {"type": "text", "text": extra_text, "size": "md", "wrap": True, "color": "#008000"}
            ]
        }
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
