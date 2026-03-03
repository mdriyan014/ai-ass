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


# ================= TELEGRAM NOTIFY =================

def notify_riyan(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message
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

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    # ================= STEP 1: AI DETECT IF OWNER NEEDED =================

    detect_prompt = [
        {
            "role": "system",
            "content": """
তুমি একটি বিশ্লেষণকারী AI।

ইউজারের মেসেজ দেখে নির্ধারণ করো:
রিয়ানের সরাসরি মনোযোগ প্রয়োজন কি না।

শুধু YES অথবা NO উত্তর দাও।
"""
        },
        {
            "role": "user",
            "content": ask
        }
    ]

    detect_payload = {
        "model": "gpt-4o-mini-ca",
        "messages": detect_prompt,
        "temperature": 0,
        "max_tokens": 5
    }

    owner_needed = False

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            detect_response = await client.post(
                CHATANYWHERE_URL,
                headers=headers,
                json=detect_payload
            )

        detect_data = detect_response.json()

        if "choices" in detect_data:
            result = detect_data["choices"][0]["message"]["content"].strip().upper()
            owner_needed = "YES" in result

    except:
        pass


    # ================= STEP 2: IF OWNER NEEDED → SEND TELEGRAM =================

    if owner_needed:

        notify_prompt = [
            {
                "role": "system",
                "content": """
তুমি Jarvis-এর মতো রিয়ানের ব্যক্তিগত সহকারী।

রিয়ানের উদ্দেশ্যে বাংলায় একটি ছোট, প্রফেশনাল এবং সম্মানজনক নোটিফিকেশন লেখো।
স্বাভাবিকভাবে বোঝাবে যে কেউ তার মনোযোগ চাইছে।
ইমোজি ব্যবহার করবে না।
"""
            },
            {
                "role": "user",
                "content": f"ইউজার বলেছে: {ask}"
            }
        ]

        notify_payload = {
            "model": "gpt-4o-mini-ca",
            "messages": notify_prompt,
            "temperature": 0.7,
            "max_tokens": 120
        }

        try:
            async with httpx.AsyncClient(timeout=20) as client:
                notify_response = await client.post(
                    CHATANYWHERE_URL,
                    headers=headers,
                    json=notify_payload
                )

            notify_data = notify_response.json()

            if "choices" in notify_data:
                notify_text = notify_data["choices"][0]["message"]["content"]
            else:
                notify_text = "রিয়ানের মনোযোগ প্রয়োজন।"

            notify_riyan(notify_text)

        except:
            pass


    # ================= STEP 3: NORMAL AI RESPONSE =================

    if mode == "detailed":
        ask += "\nGive slightly detailed explanation."
    else:
        ask += "\nAnswer short and clear."

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
            "answer": data["choices"][0]["message"]["content"]
        }

    except Exception as e:
        return {"status": False, "error": str(e)}
