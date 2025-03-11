from flask import Flask

app = Flask(__name__)

@app.route("/")  # 处理 `/` 请求
def home():
    return "Hello, this is my LINE Bot!"

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))  # Render 需要使用指定的 PORT
    app.run(host="0.0.0.0", port=port, debug=True)
