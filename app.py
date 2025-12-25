import os
import json
import requests
import threading
import time
from flask import Flask, request

app = Flask(__name__)

PAGE_ACCESS_TOKEN = "EAApvye5uWPcBQVFi6I6WYMXuCWhWbxi3de4sgfr75DZC9xQDmKrGUbg3ACRrxAmVlCs7zF0YQUZAa0KWJynKZB3giJlICtvXZCu3eJuUVxIKX60BE98c4ejqvfhNHeALBd34vnDaYwNBOg4Il4N5uK72hhkaiPu4Lbm7q5MhnDWSulQaTac4JzOj9GboVy0UZAYiH4gZDZD"
VERIFY_TOKEN = "tun123"

POLLINATIONS_TEXT_URL = "https://text.pollinations.ai/"
DATA_FILE = "user_data.json"
USER_DATA = {}

def load_data():
    global USER_DATA
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                USER_DATA = json.load(f)
            print("--- DA TAI DU LIEU TU FILE ---")
    except Exception as e:
        print(f"Loi load data: {e}")
        USER_DATA = {}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(USER_DATA, f, ensure_ascii=False)
    except Exception as e:
        print(f"Loi save data: {e}")

load_data()

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
    
    try:
        response = requests.post(
            f"{POLLINATIONS_TEXT_URL}?model=openai",
            data=full_prompt.encode('utf-8'),
            headers={'Content-Type': 'text/plain'},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.text
        else:
            print(f"API Error: {response.status_code}")
            return "Tũn đang bị lag nhẹ (Lỗi kết nối), bạn hỏi lại sau xíu nha!"
            
    except Exception as e:
        print(f"Request Error: {e}")
        return "Mạng của Tũn đang chập chờn, đợi chút nhé!"

def send_message(recipient_id, text):
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    
    if len(text) > 2000:
        chunks = [text[i:i+1900] for i in range(0, len(text), 1900)]
        for chunk in chunks:
            data = json.dumps({"recipient": {"id": recipient_id}, "message": {"text": chunk}})
            requests.post("https://graph.facebook.com/v18.0/me/messages", params=params, headers=headers, data=data)
            time.sleep(0.5)
    else:
        data = json.dumps({"recipient": {"id": recipient_id}, "message": {"text": text}})
        requests.post("https://graph.facebook.com/v18.0/me/messages", params=params, headers=headers, data=data)

def process_message_thread(sender_id, message_text):
    print(f"--- XU LY TIN NHAN TU: {sender_id} ---")
    load_data()

    if sender_id not in USER_DATA:
        USER_DATA[sender_id] = {"step": 1, "series": "", "grade": ""}
        save_data()
        send_message(sender_id, "Hế lô! Tũn đây. Cậu học sách giáo khoa nào? (Cánh diều, Kết nối tri thức...)")
        return

    user_info = USER_DATA[sender_id]
    step = user_info["step"]

    if message_text.lower() in ["reset", "lại", "bat dau", "start"]:
        USER_DATA[sender_id] = {"step": 1, "series": "", "grade": ""}
        save_data()
        send_message(sender_id, "Làm lại nhé! Cậu học sách nào?")
        return

    if step == 1:
        user_info["series"] = message_text
        user_info["step"] = 2
        save_data()
        send_message(sender_id, f"Ok sách '{message_text}'. Thế cậu học lớp mấy?")
    elif step == 2:
        user_info["grade"] = message_text
        user_info["step"] = 3
        save_data()
        send_message(sender_id, f"Duyệt! Tũn đã sẵn sàng hỗ trợ {user_info['series']} - {user_info['grade']}. Hỏi bài đi!")
    elif step == 3:
        send_message(sender_id, "Tũn đang nghĩ... 🧠")
        reply = get_pollinations_reply(message_text, user_info)
        send_message(sender_id, reply)

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
                if (event.get("message") and 
                    not event["message"].get("is_echo") and 
                    not event.get("delivery") and 
                    not event.get("read")):
                    
                    sender_id = event["sender"]["id"]
                    if event["message"].get("text"):
                        message_text = event["message"]["text"]
                        threading.Thread(target=process_message_thread, args=(sender_id, message_text)).start()
    
    return "ok", 200

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))
