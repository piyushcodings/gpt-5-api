from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import openai
import requests
import uuid

openai.api_key = "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"

app = FastAPI()

# In-memory chat history (replace with DB for production)
chat_history = {}

class ChatRequest(BaseModel):
    message: str  # required
    uid: Optional[str] = None
    file_url: Optional[str] = None
    image_url: Optional[str] = None
    generate_image: Optional[bool] = False

@app.post("/chat")
async def chat(request: ChatRequest):
    uid = request.uid or str(uuid.uuid4())

    if uid not in chat_history:
        chat_history[uid] = []

    message_to_send = request.message

    # --------------------
    # File URL processing
    # --------------------
    if request.file_url:
        try:
            resp = requests.get(request.file_url)
            resp.raise_for_status()
            file_text = resp.text[:5000]  # limit for demo
        except Exception as e:
            file_text = f"[File at {request.file_url} could not be fetched]"
        message_to_send += "\n" + file_text
        chat_history[uid].append({"role": "user", "content": file_text})

    # --------------------
    # Image URL processing
    # --------------------
    if request.image_url:
        message_to_send += f"\n[Analyze image at {request.image_url}]"

    # --------------------
    # Image Generation
    # --------------------
    if request.generate_image:
        img_resp = openai.images.generate(
            model="dall-e-3",
            prompt=message_to_send,
            size="1024x1024"
        )
        return {"uid": uid, "image_url": img_resp.data[0].url}

    # --------------------
    # GPT-5 Text / File / Image Chat
    # --------------------
    gpt_response = openai.chat.completions.create(
        model="gpt-5",
        messages=[{"role": "user", "content": message_to_send}]
    )

    chat_history[uid].append({"role": "assistant", "content": gpt_response.choices[0].message.content})

    return {"uid": uid, "response": gpt_response.choices[0].message.content}

# --------------------
# Get Chat History
# --------------------
@app.get("/history/{uid}")
async def get_history(uid: str):
    return {"uid": uid, "history": chat_history.get(uid, [])}
