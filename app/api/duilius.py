# Chatbot Duilius - Configuración Inicial

from fastapi import FastAPI, Request, APIRouter
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from openai import OpenAI
import os
from dotenv import load_dotenv

app = FastAPI()

# Cargar las variables del archivo .env
api_key = os.getenv("inventario_demo_key")

client = OpenAI(api_key=api_key)

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Configuración de Jinja2 para renderizar plantillas HTML
env = Environment(loader=FileSystemLoader('templates'))


# Servir archivos estáticos (CSS, JS, imágenes)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Ruta para renderizar el dashboard con el chatbot
@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    template = env.get_template("dashboard.html")
    return template.render()

# Endpoint para manejar consultas del chatbot
"""@app.post("/duilius-chat")
async def duilius_chat(request: Request):
    data = await request.json()
    user_message = data.get("message")

    # Lógica de respuesta de IA (simplificada)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are Duilius, an intelligent support assistant specialized in Xero integrations."},
            {"role": "user", "content": user_message}
        ]
    )

    ai_response = response['choices'][0]['message']['content']
    return JSONResponse(content={"response": ai_response})"""

@router.post("/duilius-chat")
async def duilius_chat(request: Request):
    data = await request.json()
    user_message = data.get("message")

    # Consulta a OpenAI
    try:
        # Nueva forma de invocar la API de OpenAI
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Eres Duilius, un asistente experto en conciliaciones de Xero. Responde de forma clara y profesional."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=150,
            temperature=0.7
        )
        ai_response = response.choices[0].message.content.strip()
    except Exception as e:
        ai_response = f"Ocurrió un error: {e}"

    return JSONResponse(content={"response": ai_response})

# Ruta para escalar consultas complejas a soporte humano
@app.post("/duilius-escalate")
async def escalate_to_support(request: Request):
    data = await request.json()
    user_email = data.get("email")
    issue = data.get("issue")

    # Simulación de envío de correo a soporte
    # (Aquí se integraría con un servicio real de email)
    print(f"Escalando a soporte: {user_email} - {issue}")

    return JSONResponse(content={"message": "Your request has been escalated to human support. We will contact you soon."})

"""# Iniciar la aplicación
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)"""
