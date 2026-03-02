import httpx
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse

app = FastAPI()

# 🔥 এখানে তোমার আসল ChatAnywhere API key বসাও
API_KEY = "sk-sRcjuojZqugywcfj8IY8qBgGZgEr7KWNVydiZt5QMCAY2xuf"

CHATANYWHERE_URL = "https://api.chatanywhere.tech/v1/chat/completions"

ACCESS_KEY = "dark"


@app.get("/")
async def home():
    return {
        "status": True,
        "message": "AI API Running",
        "usage": "/api/ask?key=dark&ask=hello"
    }


@app.get("/api/ask")
async def ask_ai(
    key: str = Query(...),
    ask: str = Query(...)
):
    if key != ACCESS_KEY:
        return JSONResponse(
            {"status": False, "error": "Invalid access key"},
            status_code=403
        )

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gpt-4o-mini-ca",
        "messages": [
            {"role": "system", "content": "Reply short and clear."},
            {"role": "user", "content": ask}
        ],
        "temperature": 0.5,
        "max_tokens": 200
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
