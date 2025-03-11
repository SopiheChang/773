from flask import Flask, request, jsonify
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, FlexSendMessage
import os
import datetime

app = Flask(__name__)

# 你的 LINE Bot 频道 Token & Secret（替换成你自己的）
LINE_CHANNEL_ACCESS_TOKEN = os.getenv("LINE_CHANNEL_ACCESS_TOKEN")
LINE_CHANNEL_SECRET = os.getenv("LINE_CHANNEL_SECRET")

line_bot_api = LineBotApi(LINE_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(LINE_CHANNEL_SECRET)

# 预设的天数参考值
PRESET_DAYS = [27, 38, 45, 56, 69, 76, 95, 112, 120, 130, 140, 150, 156, 167]

def find_nearest_days(day_diff):
    """找到不大于 day_diff 的最接近的值"""
    return max([d for d in PRESET_DAYS if d <= day_diff], default=PRESET_DAYS[0])

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
        day_diff = (today - input_date).days

        # 找到最接近的预设数值
        nearest_days = find_nearest_days(day_diff)

        # 生成 Flex Message
        flex_message = generate_flex_message(user_input, day_diff, nearest_days)

        # 发送 Flex Message
        line_bot_api.reply_message(event.reply_token, FlexSendMessage(alt_text="计算结果", contents=flex_message))

    except ValueError:
        # 如果输入不是正确的日期格式，则返回提示消息
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text="❌ 请输入正确的日期格式（YYYYMMDD）"))

def generate_flex_message(user_date, day_diff, nearest_days):
    """生成 Flex Message JSON，包含额外说明"""

    # 预设匹配值的额外说明
    EXTRA_DESCRIPTIONS = {
        27: "🐷 小猪刚入栏，注意适应期。",
        38: "📊 进入生长期，调整饲料配方。",
        45: "🔬 需观察生长情况，是否健康。",
        56: "🛠 可能需要做疫苗加强。",
        69: "💡 进入快速增重期。",
        76: "📈 适量增加饲料供给。",
        95: "📅 可开始初步估算市场价格。",
        112: "🏡 准备进入育肥期。",
        120: "🐖 可考虑分栏管理。",
        130: "💰 可开始评估出栏定价。",
        140: "📦 可能进入预售阶段。",
        150: "🚛 预计出栏运输安排。",
        156: "📌 需联系买家确认交付。",
        167: "📝 统计育肥数据，优化流程。",
    }

    # 获取匹配值的额外说明（如果没有则为空）
    extra_text = EXTRA_DESCRIPTIONS.get(nearest_days, "🔍 无额外说明")

    return {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {"type": "text", "text": "📅 你输入的日期：", "weight": "bold", "size": "md"},
                {"type": "text", "text": f"{user_date}", "size": "lg", "color": "#00bfff"},
                {"type": "separator"},
                {"type": "text", "text": f"⏳ 距今 {day_diff} 天", "size": "md"},
                {"type": "text", "text": f"🎯 匹配值：{nearest_days} 天", "weight": "bold", "size": "lg", "color": "#ff5555"},
                {"type": "separator"},
                {"type": "text", "text": extra_text, "size": "md", "wrap": True, "color": "#008000"}
            ]
        }
    }

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
