from fastapi import APIRouter, FastAPI, HTTPException, Depends
from pydantic import BaseModel
import openai
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Inicializar FastAPI
app = FastAPI()

# Configurar OpenAI
openai.api_key = os.getenv("OPENAI_API_KEY")

# Crear el router para este módulo
router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

# Modelo de entrada
class QueryRequest(BaseModel):
    query: str

# Definición del esquema de la base de datos
DATABASE_SCHEMA = """
Base de datos relacionada para consultas SQL:
...
(Tu esquema previamente definido con tablas y relaciones)
..."""

# Función para generar el prompt
def build_prompt(user_query: str) -> str:
    return f"""
    Eres un asistente experto en SQL. Basándote en la siguiente estructura de base de datos, genera una consulta SQL válida para responder la pregunta del usuario.
    
    {DATABASE_SCHEMA}
    
    Pregunta: {user_query}
    
    Formatea la respuesta en JSON con los siguientes campos:
    {{
      "respuesta": "si/no",
      "tipo_respuesta": "tabla/diferencia/porcentaje/...",
      "tipo_grafica": "ninguna/barras/tendencia/pastel/...",
      "query": "SQL generado",
      "titulo": "Explicación breve"
    }}
    """

# Endpoint para generar consultas SQL
@app.post("/generate-sql")
async def generate_sql(request: QueryRequest):
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="La consulta no puede estar vacía.")

    prompt = build_prompt(request.query)

    if not prompt.strip():
        raise HTTPException(status_code=400, detail="El prompt generado está vacío.")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente experto en SQL."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )

        result = response["choices"][0]["message"]["content"]
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al generar SQL: {str(e)}")
