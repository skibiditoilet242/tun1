import os
import json
import requests
import threading
import time
import urllib.parse
from flask import Flask, request

app = Flask(__name__)

PAGE_ACCESS_TOKEN = "EAApvye5uWPcBQVFi6I6WYMXuCWhWbxi3de4sgfr75DZC9xQDmKrGUbg3ACRrxAmVlCs7zF0YQUZAa0KWJynKZB3giJlICtvXZCu3eJuUVxIKX60BE98c4ejqvfhNHeALBd34vnDaYwNBOg4Il4N5uK72hhkaiPu4Lbm7q5MhnDWSulQaTac4JzOj9GboVy0UZAYiH4gZDZD"
VERIFY_TOKEN = "tun123"
POLLINATIONS_TEXT_URL = "https://text.pollinations.ai/"
POLLINATIONS_IMAGE_URL = "https://pollinations.ai/p/"
DATA_FILE = "user_data.json"
PREFIX = "!"
USER_DATA = {}

def load_data():
    global USER_DATA
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                USER_DATA = json.load(f)
    except Exception:
        USER_DATA = {}

def save_data():
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(USER_DATA, f, ensure_ascii=False)
    except Exception:
        pass

load_data()

def get_pollinations_reply(text, user_id):
    user_info = USER_DATA.get(user_id, {})
    mode = user_info.get("mode", "tutor")
    
    if mode == "fun":
        history = user_info.get("history", [])
        history_str = "\n".join(history[-10:])
        persona = (
            "Bạn là Tũn, một AI siêu hài hước, lầy lội, đậm chất Gen Z. "
            "Bạn không phải là gia sư nữa, mà là một người bạn thân thiết, thích cà khịa vui vẻ. "
            "Nhiệm vụ: Trò chuyện làm người dùng cười, dùng teencode, emoji thoải mái. "
            "Khả năng đặc biệt: Ghi nhớ các thông tin người dùng đã nói trong đoạn chat để cá nhân hóa câu trả lời. "
            f"Lịch sử chat gần đây:\n{history_str}"
        )
    else:
        series = user_info.get("series", "chung")
        grade = user_info.get("grade", "chung")
        persona = (
            f"Bạn là Tũn, gia sư toàn năng, nghiêm túc. "
            f"Học sinh đang học sách '{series}' lớp '{grade}'. "
            "Nhiệm vụ: Giải đáp học tập chi tiết, dễ hiểu, step-by-step. "
            "QUY TẮC: Luôn dùng Tiếng Việt chuẩn mực."
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
    except Exception:
        pass
    return "Tũn đang lag nhẹ, đợi xíu nha!"

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

def send_image(recipient_id, prompt):
    encoded_prompt = urllib.parse.quote(prompt)
    image_url = f"{POLLINATIONS_IMAGE_URL}{encoded_prompt}"
    params = {"access_token": PAGE_ACCESS_TOKEN}
    headers = {"Content-Type": "application/json"}
    data = json.dumps({
        "recipient": {"id": recipient_id},
        "message": {
            "attachment": {
                "type": "image",
                "payload": {
                    "url": image_url, 
                    "is_reusable": True
                }
            }
        }
    })
    requests.post("https://graph.facebook.com/v18.0/me/messages", params=params, headers=headers, data=data)

def handle_command(sender_id, command):
    cmd_parts = command[1:].split(" ", 1)
    cmd = cmd_parts[0].lower().strip()
    args = cmd_parts[1] if len(cmd_parts) > 1 else ""
    
    if sender_id not in USER_DATA:
        USER_DATA[sender_id] = {"mode": "tutor", "step": 1, "series": "", "grade": "", "history": []}

    if cmd == "help":
        msg = (
            "📚 MENU CỦA TŨN 📚\n"
            "👉 !fun : Bật chế độ hài hước, lầy lội.\n"
            "👉 !tutor : Bật chế độ gia sư nghiêm túc.\n"
            "👉 !img <mô tả> : Vẽ tranh (VD: !img mèo lái xe).\n"
            "👉 !reset : Xóa não, học lại từ đầu.\n"
            "👉 !info : Thông tin về Tũn."
        )
        send_message(sender_id, msg)
        return True
    
    elif cmd == "fun":
        USER_DATA[sender_id]["mode"] = "fun"
        save_data()
        send_message(sender_id, "🤪 Đã bật chế độ Hài Hước! Tũn nay sẽ quậy tới bến luôn nha!")
        return True

    elif cmd == "tutor":
        USER_DATA[sender_id]["mode"] = "tutor"
        save_data()
        send_message(sender_id, "🧐 Đã bật chế độ Gia Sư. Xin mời em đặt câu hỏi học tập.")
        return True

    elif cmd == "img" or cmd == "anh":
        if not args:
            send_message(sender_id, "Nhập mô tả ảnh đi nè (VD: !img con chó).")
        else:
            send_message(sender_id, f"Đang vẽ '{args}'... Đợi xíu nhen! 🎨")
            send_image(sender_id, args)
        return True

    elif cmd == "reset":
        USER_DATA[sender_id] = {"mode": "tutor", "step": 1, "series": "", "grade": "", "history": []}
        save_data()
        send_message(sender_id, "Đã reset! Làm lại cuộc đời nha.")
        return True
        
    elif cmd == "info":
        send_message(sender_id, "Tũn là Bot AI đa năng. Lúc thì nghiêm túc dạy học, lúc thì lầy lội chém gió.")
        return True
        
    return False

def process_message_thread(sender_id, message_text):
    load_data()

    if message_text.startswith(PREFIX):
        if handle_command(sender_id, message_text):
            return

    if sender_id not in USER_DATA:
        USER_DATA[sender_id] = {"mode": "tutor", "step": 1, "series": "", "grade": "", "history": []}
        save_data()
        send_message(sender_id, "Hế lô! Tũn đây. Gõ !help để xem cách dùng, hoặc trả lời Tũn biết cậu học sách gì nào?")
        return

    user_info = USER_DATA[sender_id]
    mode = user_info.get("mode", "tutor")

    if mode == "fun":
        user_info.setdefault("history", []).append(f"User: {message_text}")
        send_message(sender_id, "...")
        reply = get_pollinations_reply(message_text, sender_id)
        user_info["history"].append(f"Tũn: {reply}")
        if len(user_info["history"]) > 20:
            user_info["history"] = user_info["history"][-20:]
        save_data()
        send_message(sender_id, reply)
        return

    step = user_info.get("step", 1)

    if step == 1:
        user_info["series"] = message_text
        user_info["step"] = 2
        save_data()
        send_message(sender_id, f"Ghi nhận sách '{message_text}'. Thế cậu học lớp mấy?")
        
    elif step == 2:
        user_info["grade"] = message_text
        user_info["step"] = 3
        save_data()
        send_message(sender_id, f"Duyệt! Tũn sẽ hỗ trợ chương trình {user_info['series']} - {user_info['grade']}. Hỏi bài đi!")
        
    elif step == 3:
        if message_text.lower() in ["đổi sách", "chọn lại"]:
            USER_DATA[sender_id] = {"mode": "tutor", "step": 1, "series": "", "grade": "", "history": []}
            save_data()
            send_message(sender_id, "Okie, chọn lại sách nào?")
            return

        send_message(sender_id, "Tũn đang giải... ✍️")
        reply = get_pollinations_reply(message_text, sender_id)
        send_message(sender_id, reply)

@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return "Sai token", 403

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
