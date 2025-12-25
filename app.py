import os
import json
import requests
from flask import Flask, request

app = Flask(__name__)

# --- CẤU HÌNH ---
# Dán Token Facebook của ông vào đây
PAGE_ACCESS_TOKEN = "EAApvye5uWPcBQT5yZAVL9XcncvlAt5UIpICR0hS6f3H7jA5mq2GyC9W4auMc6OSnVDQ946TIkEROSckaw5MPbPZB7f4uaCUPCF5qAR1k55ZBIh9ZAdlZBingzI1jFd3Bdy1nxWSC8Jg7JDoqbyUXQR1rPRQ6us1EAALcpa34VbOhzGunOSgentLmwfVw0oSGNAPh40u0lYhLe8K4hCHD3VJ1iHi2EE6Nn2LMZD"
# Mã xác minh (nhớ cái này để điền vào Facebook)
VERIFY_TOKEN = "tun123"
# ----------------

POLLINATIONS_TEXT_URL = "https://text.pollinations.ai/"
USER_DATA = {}

def get_pollinations_reply(text, user_context):
    series = user_context.get("series", "chung")
    grade = user_context.get("grade", "chung")
    persona = (
        f"Bạn là Tũn, gia sư toàn năng, vui tính. "
        f"Học sinh đang học sách '{series}' lớp '{grade}'. "
        "Nhiệm vụ: Giải đáp mọi môn học (Toán, Lý, Hóa, Văn, Anh...) chi tiết, dễ hiểu. "
        "QUY TẮC: Luôn dùng Tiếng Việt. Giải step-by-step."
    )
    full_prompt = f"{persona}\n\nUser: {text}\nTũn:"
    headers = {'Content-Type': 'text/plain'}
    
    try:
        url = f"{POLLINATIONS_TEXT_URL}?model=openai"
        response = requests.post(url, data=full_prompt.encode('utf-8'), headers=headers, timeout=20)
        if response.status_code == 200:
            return response.text
    except:
        pass
    return "Tũn đang lag, đợi xíu hỏi lại nha!"

def handle_message(sender_id, message_text):
    if sender_id not in USER_DATA:
        USER_DATA[sender_id] = {"step": 1, "series": "", "grade": ""}
        send_message(sender_id, "Hế lô! Tũn đây. Cậu học sách giáo khoa nào? (Cánh diều, Kết nối tri thức...)")
        return

    user_info = USER_DATA[sender_id]
    step = user_info["step"]

    if message_text.lower() in ["reset", "lại"]:
        USER_DATA[sender_id] = {"step": 1, "series": "", "grade": ""}
        send_message(sender_id, "Làm lại nhé! Cậu học sách nào?")
        return

    if step == 1:
        user_info["series"] = message_text
        user_info["step"] = 2
        send_message(sender_id, f"Ok sách '{message_text}'. Thế cậu học lớp mấy?")
    elif step == 2:
        user_info["grade"] = message_text
        user_info["step"] = 3
        send_message(sender_id, f"Duyệt! Tũn đã sẵn sàng hỗ trợ {user_info['series']} - {user_info['grade']}. Hỏi bài đi!")
    elif step == 3:
        send_message(sender_id, "Tũn đang nghĩ... 🧠")
        reply = get_pollinations_reply(message_text, user_info)
        send_message(sender_id, reply)

def send_message(recipient_id, text):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    if len(text) > 2000: text = text[:1990] + "..."
    data = json.dumps({"recipient": {"id": recipient_id}, "message": {"text": text}})
    requests.post("https://graph.facebook.com/v18.0/me/messages", params=params, headers=headers, data=data)

@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Sai token roi", 403

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()
    if data["object"] == "page":
        for entry in data["entry"]:
            for event in entry["messaging"]:
                if event.get("message") and event["message"].get("text"):
                    handle_message(event["sender"]["id"], event["message"]["text"])
    return "ok", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
