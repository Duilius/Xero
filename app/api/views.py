# api/views.py
from fastapi import FastAPI, APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

app = FastAPI()
# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/matrix")
async def matrix_view(request: Request):
   return templates.TemplateResponse(
       "accounts/cross_matrix.html",
       {
           "request": request,
           "page_title": "Análisis Cruzado de Cuentas"
       }
   )

# Agregamos en main.py
from app.api.views import router as views_router
app.include_router(views_router)