from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import os
import datetime
import requests
import pandas as pd

app = Flask(__name__)

# 你的 LINE Bot 频道 Token & Secret
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")
GITHUB_FILE_URL = "https://raw.githubusercontent.com/SopiheChang/773/main/data.xlsx"

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 预设的天数参考值
PRESET_DAYS = [27, 38, 45, 56, 69, 76, 95, 112, 120, 130, 140, 150, 156, 167]

def find_nearest_days(day_diff):
    """找到不大于 day_diff 的最接近的值"""
    return max([d for d in PRESET_DAYS if d <= day_diff], default=PRESET_DAYS[0])

def read_excel_data():
    """从 GitHub 下载并读取 Excel 数据"""
    response = requests.get(GITHUB_FILE_URL)
    with open("data.xlsx", "wb") as file:
        file.write(response.content)
    
    df = pd.read_excel("data.xlsx")
    data_dict = {}

    for _, row in df.iterrows():
        key = row.iloc[0]  # 第一列作为 key
        value = row.iloc[1]  # 第二列作为 value
        if key in data_dict:
            data_dict[key].append(value)
        else:
            data_dict[key] = [value]
    
    return data_dict

@app.route("/", methods=["GET"])
def home():
    return "Hello, this is my LINE Bot!"

@app.route("/webhook", methods=["POST"])
def webhook():
    """处理 LINE Webhook 请求"""
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)

    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        return "Invalid signature", 400

    return "OK", 200

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    """处理收到的文本消息"""
    user_input = event.message.text.strip()

    try:
        # 解析日期并计算天数差
        input_date = datetime.datetime.strptime(user_input, "%Y%m%d").date()
        today = datetime.date.today()
        day_diff = (today - input_date).days + 27

        # 找到最接近的预设数值
        nearest_days = find_nearest_days(day_diff)

        # 从 Excel 读取数据
        excel_data = read_excel_data()
        extra_text = "\n".join([str(value) for value in excel_data.get(nearest_days, ["🔍 无额外说明"])])

        # 生成 Flex Message
        flex_message = generate_flex_message(user_input, day_diff, nearest_days, extra_text)

        # 发送 Flex Message
        line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="計算結果", contents=flex_message))

    except ValueError:
        # 如果输入格式错误，则返回提示消息
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 請輸入正確的日期格式（YYYYMMDD）"))

def generate_flex_message(user_date, day_diff, nearest_days, extra_text):
    """生成 Flex Message JSON，包含额外说明"""
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
                {"type": "text", "text": extra_text, "size": "md", "wrap": True, "color": "#008000"}
            ]
        }
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
