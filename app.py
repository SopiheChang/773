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
    url = "https://raw.githubusercontent.com/SopiheChang/773/main/data.xlsx"
    response = requests.get(url)
    with open("data.xlsx", "wb") as file:
        file.write(response.content)
    
    df = pd.read_excel("data.xlsx")
    data_dict = {}
    
    for _, row in df.iterrows():
        key = row[0]  # Excel 第一列
        value = row[1]  # Excel 第二列
        if key in data_dict:
            data_dict[key].append((row[0], row[1]))  # 儲存多筆資料
        else:
            data_dict[key] = [(row[0], row[1])]
    
    return data_dict


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
        day_diff = (today - input_date +27).days

        # 找到最接近的預設數值
        nearest_days = find_nearest_days(day_diff)

        # 從 Excel 讀取數據（確保這部分代碼存在）
        excel_data = read_excel_data()

        # 獲取額外資訊
        extra_text = "\n".join([f"{row[0]}: {row[1]}" for row in excel_data.get(nearest_days, [])])

        # 生成 Flex Message
        flex_message = generate_flex_message(user_input, day_diff, nearest_days, extra_text)

        # 发送 Flex Message
        reply_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[FlexSendMessage(alt_text="計算結果", contents=flex_message)]
        )
        messaging_api.reply_message(reply_request)

    except ValueError:
        # 如果輸入不是正確的日期格式，則返回提示消息
        reply_request = ReplyMessageRequest(
            reply_token=event.reply_token,
            messages=[TextMessage(text="❌ 請輸入正確的日期格式（YYYYMMDD）")]
        )
        messaging_api.reply_message(reply_request)
        
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
