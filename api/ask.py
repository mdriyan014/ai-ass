import httpx
import requests
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from time import time

app = FastAPI()

# ================= CONFIG =================

API_KEY = "sk-Vjxdtfh6amyk2hcFI9cpib9owQ5LogPFIAfm6UjjStK3Wo3U"
CHATANYWHERE_URL = "https://api.chatanywhere.tech/v1/chat/completions"

ACCESS_KEY = "dark"

TELEGRAM_BOT_TOKEN = "8460295947:AAHMpJ9LxEyBFJqAWVPqGQAaFddXRd_qWtE"
TELEGRAM_CHAT_ID = "7980571462"

RATE_LIMIT = 12
RATE_WINDOW = 60

rate_store = {}

# 🔥 তোমার SYSTEM PROMPT এখানে বসাবে
SYSTEM_PROMPT = """ 
<PUT YOUR SYSTEM PROMPT HERE>
"""

# ================= RATE LIMIT =================

def check_rate(ip):
    now = int(time())
    bucket = rate_store.get(ip, [])
    bucket = [t for t in bucket if t > now - RATE_WINDOW]

    if len(bucket) >= RATE_LIMIT:
        return False

    bucket.append(now)
    rate_store[ip] = bucket
    return True

# ================= LANGUAGE DETECT =================

def detect_language(text):
    if any("\u0980" <= c <= "\u09FF" for c in text):
        return "bn"
    return "en"

# ================= SUMMON DETECT =================

def check_summon(text):
    text = text.lower()

    triggers = [
        "call riyan",
        "riyan ke dak",
        "riyan ke dako",
        "riyan ke bolo",
        "riyan ko bulao",
        "summon riyan",
        "dak riyan",
        "ডাক রিয়ান",
        "রিয়ান কে ডাক",
        "রিয়ানকে ডাক",
        "রিয়ানকে বল",
        "রিয়ানকে জানাও"
    ]

    return any(trigger in text for trigger in triggers)

# ================= TELEGRAM NOTIFY =================

def notify_riyan(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": f"🔔 Riyan Summoned!\n\nUser said:\n{message}"
        }
        requests.post(url, data=payload, timeout=10)
    except:
        pass

# ================= ROUTES =================

@app.get("/")
async def home():
    return {
        "status": True,
        "message": "Monkey D. Luffy AI Running",
        "usage": "/api/ask?key=dark&ask=hello"
    }

@app.get("/api/ask")
async def ask_ai(
    key: str = Query(...),
    ask: str = Query(...),
    mode: str = Query("short"),
    request_ip: str = Query("unknown")
):
    if key != ACCESS_KEY:
        return JSONResponse({"status": False, "error": "Invalid access key"}, status_code=403)

    if not check_rate(request_ip):
        return JSONResponse({"status": False, "error": "Rate limit exceeded"}, status_code=429)

    language = detect_language(ask)

    # 🔥 Summon system
if check_summon(ask):

    notify_prompt = [
        {
            "role": "system",
            "content": "Write a short intelligent notification message to inform Riyan that someone is calling him. Keep it short and natural."
        },
        {
            "role": "user",
            "content": f"User message: {ask}"
        }
    ]

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload_notify = {
        "model": "gpt-4o-mini-ca",
        "messages": notify_prompt,
        "temperature": 0.7,
        "max_tokens": 100
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response_notify = await client.post(
                CHATANYWHERE_URL,
                headers=headers,
                json=payload_notify
            )

        data_notify = response_notify.json()

        if "choices" in data_notify:
            notify_text = data_notify["choices"][0]["message"]["content"]
        else:
            notify_text = "Riyan, someone is calling you."

    except:
        notify_text = "Riyan, someone is calling you."

    notify_riyan(notify_text)

    if language == "bn":
        return {
            "status": True,
            "answer": "আমি রিয়ানকে জানিয়ে দিয়েছি।"
        }
    else:
        return {
            "status": True,
            "answer": "I have notified Riyan."
        }

    # Mode control
    if mode == "detailed":
        ask = ask + "\nGive a slightly detailed explanation."
    else:
        ask = ask + "\nAnswer short and clear."

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-mini-ca",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": ask}
        ],
        "temperature": 0.5,
        "max_tokens": 220
    }

    try:
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.post(
                CHATANYWHERE_URL,
                headers=headers,
                json=payload
            )

        data = response.json()

        if "choices" not in data:
            return {"status": False, "error": data}

        return {
            "status": True,
            "language": language,
            "mode": mode,
            "answer": data["choices"][0]["message"]["content"]
        }

    except Exception as e:
        return {"status": False, "error": str(e)}
