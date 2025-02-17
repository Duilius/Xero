from fastapi import APIRouter, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import openai
import os
from dotenv import load_dotenv
from pydantic import BaseModel

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/chatbot")
async def chatbot_page(request: Request):
    return templates.TemplateResponse("chatbot/chatbot.html", {"request": request})


#************ CHATBOT ==> PREGUNTAS SUGERIDAS ****************************
# Load environment variables
load_dotenv()

# Configure OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

class ChatRequest(BaseModel):
    question: str

@router.post("/chatbot/ask")
async def ask_chatbot(request: ChatRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    try:
        answer = generate_openai_response(question)
        return f'<div class="chatbot-message chatbot">{answer}</div>'
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def generate_openai_response(question: str) -> str:
    """Generates a response using OpenAI API."""
    response = openai.ChatCompletion.create(
        model="gpt-4",  # Use preferred model
        messages=[
            {"role": "system", "content": "You are an expert assistant in business analysis."},
            {"role": "user", "content": question}
        ]
    )
    return response["choices"][0]["message"]["content"]
