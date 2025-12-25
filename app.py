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
PREFIX = "!"
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
        f"Bạn là Tũn, một gia sư AI vui tính nhưng rất nghiêm túc trong học tập. "
        f"Học sinh hiện tại đang học lớp '{grade}', bộ sách '{series}'. "
        "Nhiệm vụ: Giải đáp mọi thắc mắc về Toán, Lý, Hóa, Văn, Anh... một cách chi tiết, dễ hiểu, step-by-step. "
        "QUY TẮC: Luôn dùng Tiếng Việt. Không nói tục. Nếu gặp câu hỏi không liên quan đến học tập, hãy lái về chuyện học hành một cách khéo léo."
    )

    payload = {
        "messages": [
            {"role": "system", "content": persona},
            {"role": "user", "content": text}
        ],
        "model": "openai",
        "json": False
    }
    
    try:
        response = requests.post(
            POLLINATIONS_TEXT_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            return response.text
        else:
            print(f"API Error: {response.status_code} - {response.text}")
            return "Tũn đang bị lỗi kết nối với vũ trụ tri thức rồi. Bạn thử lại câu ngắn hơn xem?"
            
    except Exception as e:
        print(f"Request Error: {e}")
        return "Mạng lag quá, Tũn load không nổi!"

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

def handle_command(sender_id, command):
    cmd = command[1:].lower().strip()
    
    if cmd == "help":
        msg = (
            "📚 HƯỚNG DẪN SỬ DỤNG TŨN 📚\n\n"
            "Các lệnh cơ bản:\n"
            "👉 !reset : Xóa thông tin sách/lớp để chọn lại từ đầu.\n"
            "👉 !info : Xem thông tin về gia sư Tũn.\n"
            "👉 !ping : Kiểm tra xem Tũn có đang ngủ gật không.\n"
            "👉 !help : Xem bảng này.\n\n"
            "Cứ nhắn tin bình thường để hỏi bài nhé!"
        )
        send_message(sender_id, msg)
        return True
    
    elif cmd == "reset":
        USER_DATA[sender_id] = {"step": 1, "series": "", "grade": ""}
        save_data()
        send_message(sender_id, "Đã xóa bộ nhớ! 🧹\nGiờ chúng ta làm lại nhé. Cậu đang học bộ sách giáo khoa nào?")
        return True
        
    elif cmd == "info":
        send_message(sender_id, "Tớ là Tũn, Gia sư AI chạy bằng cơm (điện). Tớ cân tất cả các môn từ Toán đến Văn. Nhớ hỏi bài nha đừng hỏi linh tinh!")
        return True
        
    elif cmd == "ping":
        send_message(sender_id, "Pong! 🏓 Tũn vẫn đang trực chiến!")
        return True
        
    return False

def process_message_thread(sender_id, message_text):
    print(f"--- NHAN: {message_text} (ID: {sender_id}) ---")
    load_data()

    if message_text.startswith(PREFIX):
        if handle_command(sender_id, message_text):
            return

    if sender_id not in USER_DATA:
        USER_DATA[sender_id] = {"step": 1, "series": "", "grade": ""}
        save_data()
        send_message(sender_id, "Hế lô! Tũn đây 👋\nĐể Tũn chỉ bài cho chuẩn, cậu đang học bộ sách nào? (Cánh diều, Kết nối tri thức...)")
        return

    user_info = USER_DATA[sender_id]
    step = user_info["step"]

    if step == 1:
        user_info["series"] = message_text
        user_info["step"] = 2
        save_data()
        send_message(sender_id, f"Ghi nhận sách '{message_text}'. 📚\nThế cậu đang học lớp mấy?")
        
    elif step == 2:
        user_info["grade"] = message_text
        user_info["step"] = 3
        save_data()
        send_message(sender_id, f"Tuyệt! Tũn sẽ hỗ trợ chương trình {user_info['series']} - {user_info['grade']}.\nGiờ cậu gửi bài tập qua đây, môn nào cũng được!")
        
    elif step == 3:
        if message_text.lower() in ["đổi sách", "chọn lại", "reset"]:
            USER_DATA[sender_id] = {"step": 1, "series": "", "grade": ""}
            save_data()
            send_message(sender_id, "Okie, chọn lại sách nào?")
            return

        send_message(sender_id, "Tũn đang giải... ✍️")
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
