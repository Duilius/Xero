from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from openai import OpenAI
from app.core.prompts.classifier_prompt import CLASSIFIER_PROMPT
from app.services.query_executor import execute_query
import json
import traceback
import os

client = OpenAI(
    api_key=os.getenv('inventario_demo_key')
)

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])


@router.post("/process-query")
async def process_query(request: Request):
    try:
        data = await request.json()
        user_message = data.get("message")
        
        if not user_message:
            return JSONResponse(
                content={
                    "success": False,
                    "error": "No message provided"
                },
                status_code=400
            )

        # Debug print
        print(f"Received message: {user_message}")
        
        # 1. Obtener clasificación y análisis de OpenAI
        try:
            response = client.chat.completions.create(
                #model="gpt-4-turbo-preview",
                model="gpt-4-turbo",
                messages=[
                    {"role": "system", "content": CLASSIFIER_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                temperature=0.1,
                #response_format={"type": "json"}
                response_format={"type": "json_object"}  # Cambiado de 'json' a 'json_object'
            )
            # Debug print
            print(f"OpenAI response: {response.choices[0].message.content}")
            
        except Exception as e:
            print(f"OpenAI error: {str(e)}")
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"OpenAI error: {str(e)}"
                },
                status_code=500
            )

        # 2. Parsear respuesta de OpenAI
        try:
            classification = json.loads(response.choices[0].message.content)
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {str(e)}")
            return JSONResponse(
                content={
                    "success": False,
                    "error": f"Failed to parse OpenAI response: {str(e)}"
                },
                status_code=500
            )

        # Debug print
        print(f"Classification: {classification}")
        
        # 3. Procesar según el tipo de consulta
        if classification["can_query"] == "yes":
            try:
                # Ejecutar query
                query_result = execute_query(classification["query"])  # Ya no es async
                return JSONResponse(content={
                    "success": True,
                    "data": query_result["data"],
                    "row_count": query_result["row_count"],
                    "metadata": classification
                })
            except Exception as e:
                print(f"Query execution error: {str(e)}")
                return JSONResponse(
                    content={
                        "success": False,
                        "error": f"Query execution failed: {str(e)}"
                    },
                    status_code=500
                )
        
        # 4. Si no requiere query, retornar solo la clasificación
        return JSONResponse(content={
            "success": True,
            "metadata": classification
        })
        
    except Exception as e:
        print(f"General error: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return JSONResponse(
            content={
                "success": False,
                "error": f"Internal server error: {str(e)}"
            },
            status_code=500
        )