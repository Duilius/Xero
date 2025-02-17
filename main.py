import httpx
from datetime import datetime
from fastapi import FastAPI, Request, Query
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings
from app.api import auth, users, orgs, xero
from app.core.middlewares import AuthMiddleware
from app.core.template_filters import format_number
from app.api import htmx_views
from app.api import duilius  # Importa el router de Duilius
from app.api import loans
from app.api import balance  # Nuevo import
from app import codigos_internos_xero
from app.api import accounts
from app.routers import chatbot_queries
from app.routers import chat_generate_sql
from app.routers.chat_classifier import router as classifier_router
import random
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.models.chat_models import ChatClient
from app.services.xero_balance_service import router as xero_balance_router
from fastapi import FastAPI, HTTPException, Depends
from app.db.database import get_db
from app.models import AccountMapping
from app.models import Organization
import os
import requests
from app.services.xero_auth_service import XeroAuthService
from app.models.xero_token import XeroToken
from app.routers import chatbot  # Importa el router del chatbot

#from app.core.middlewares import authenticate_user

app = FastAPI(
    title="Xero Data Extractor",
    description="Cloud service for Xero data extraction and analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://xero.dataextractor.cloud"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication Middleware
app.middleware("http")(AuthMiddleware())

# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Add custom filters
templates.env.filters["format_number"] = format_number

# Root path
@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )

# ******** PARA PROCESS BALLANCE ******** PARA PROCESS BALLANCE ******** PARA PROCESS BALLANCE ******** PARA PROCESS BALLANCE 
@app.get("/api/account-mapping/{tenant_id}/{account_code}")
def get_account_mapping(tenant_id: str, account_code: str, db: Session = Depends(get_db)):
    # Buscar la organización usando el slug (tenant_id)
    organization = db.query(Organization).filter(Organization.slug == tenant_id).first()
    if not organization:
        raise HTTPException(status_code=404, detail="Organización no encontrada")

    # Buscar el mapeo de la cuenta en xero_account_mappings
    mapping = (
        db.query(AccountMapping)
        .filter(AccountMapping.organization_id == organization.id, AccountMapping.account_code == account_code)
        .first()
    )
    
    if not mapping:
        raise HTTPException(status_code=404, detail="Mapping de cuenta no encontrado")

    return {
        "account_id": mapping.account_id,
        "account_code": mapping.account_code,
        "account_name": mapping.account_name,
        "account_type": mapping.account_type,
        "organization_id": organization.id,
        "tenant_id": tenant_id
    }

# ********** PARA PROCESS BALANCE ********** PARA PROCESS BALANCE ********** PARA PROCESS BALANCE ********** PARA PROCESS BALANCE
"""
Este endpoint consulta el balance de una cuenta específica en Xero y lo devuelve.
"""
XERO_API_URL = "https://api.xero.com/api.xro/2.0/Reports/BalanceSheet"  # URL de Xero
XERO_ACCESS_TOKEN = os.getenv("XERO_ACCESS_TOKEN")  # Acceso a Xero

# ✅ Función para extraer el saldo desde la data del balance de Xero
def get_balance_from_xero_data(xero_data, account_id):
    try:
        for section in xero_data.get("Reports", [])[0].get("Rows", []):
            for row in section.get("Rows", []):
                cells = row.get("Cells", [])
                if len(cells) >= 2:  # Asegurarnos que hay al menos 2 celdas
                    # Primera celda (cells[0]) es el nombre/descripción
                    # Segunda celda (cells[1]) es el valor
                    if cells[0].get("Attributes", [{}])[0].get("Value") == account_id:
                        balance_str = cells[1].get("Value", "0")
                        # Limpiar el string de balance antes de convertir
                        balance_str = balance_str.replace(",", "").replace("$", "")
                        try:
                            return {
                                "account_id": account_id,
                                "balance": float(balance_str) if balance_str.strip() else 0,
                                "account_name": cells[0].get("Value", ""),
                                "message": "No Transactions" if float(balance_str or 0) == 0 else None
                            }
                        except ValueError:
                            print(f"No se pudo convertir el valor '{balance_str}' a float")
                            return {
                                "account_id": account_id,
                                "balance": 0,
                                "account_name": cells[0].get("Value", ""),
                                "message": "No Transactions"
                            }
    except Exception as e:
        print(f"Error procesando balance: {str(e)}")
        
    return {
        "account_id": account_id,
        "balance": 0,
        "account_name": "",
        "message": "No Transactions"
    }


# ✅ Endpoint para obtener el balance de una cuenta específica
@app.get("/xero/account-balance/{account_id}")
async def get_account_balance(
   account_id: str,
   tenant_id: str = Query(..., description="Xero tenant ID"),
   date: str = Query(..., description="Balance date in YYYY-MM-DD format"),
   xero_auth_service: XeroAuthService = Depends(),
   db: Session = Depends(get_db)
):
   """
   Obtiene el saldo de una cuenta específica en Xero en una fecha determinada.
   """
   try:
       print(f"Processing request for account: {account_id}, tenant: {tenant_id}, date: {date}")
       
       # Obtener y verificar token para este tenant
       token_entry = db.query(XeroToken).filter_by(tenant_id=tenant_id).first()
       if not token_entry:
           raise HTTPException(status_code=404, detail="Token not found")
       
       # Refrescar token si es necesario
       token = await xero_auth_service.refresh_token_if_needed(token_entry, db)
       
       # Llamar a Xero con el token correcto
       headers = {
           "Authorization": f"Bearer {token_entry.access_token}",
           "Xero-tenant-id": tenant_id,
           "Accept": "application/json"
       }

       async with httpx.AsyncClient() as client:
           response = await client.get(
               XERO_API_URL,
               headers=headers,
               params={"date": date}
           )

           print(f"Xero API response status: {response.status_code}")
           if response.status_code == 200:
               print(f"Response preview: {response.text[:500]}...")
           else:
               print(f"Error response: {response.text}")

           if response.status_code != 200:
               raise HTTPException(
                   status_code=response.status_code,
                   detail=f"Error from Xero: {response.text}"
               )

           xero_data = response.json()
           saldo = get_balance_from_xero_data(xero_data, account_id)
           
           if saldo is None:
               raise HTTPException(status_code=404, detail="Balance not found for this account")

           print(f"Balance found for account {account_id}: {saldo}")
           return saldo

   except Exception as e:
       print(f"Error getting balance: {str(e)}")
       print(f"Full error details: {repr(e)}")
       raise HTTPException(status_code=500, detail=str(e))


# **********************************    GROWTH ACCOUNTING FIRM     ****************  GROWTH ACCOUNTING FIRM  **********
@app.get("/growth")
async def growth(request: Request):
    return templates.TemplateResponse(
        "/webs_taxes/growth_business.html",
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )


# ********************************** DEMO's WEB TAXES - SERVICES               **********************************
@app.get("/mobility")
async def mobility(request: Request):
    return templates.TemplateResponse(
        "/webs_taxes/mobility.html",
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )

@app.get("/mobility2")
async def mobility2(request: Request):
    return templates.TemplateResponse(
        "/webs_taxes/mobility2.html",
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )


@app.get("/mobility3")
async def mobility3(request: Request):
    return templates.TemplateResponse(
        "/webs_taxes/mobility3.html",
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )

@app.get("/mobility4")
async def mobility4(request: Request):
    return templates.TemplateResponse(
        "/webs_taxes/mobility4.html",
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )

@app.get("/mobility5")
async def mobility5(request: Request):
    return templates.TemplateResponse(
        "/webs_taxes/mobility5.html",
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )


@app.get("/mobility6")
async def mobility6(request: Request):
    return templates.TemplateResponse(
        "/webs_taxes/mobility6.html",
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )

@app.get("/contadores/freemiun")
async def freemiun(request: Request):
    return templates.TemplateResponse(
        "/components/contadores/freemiun_neutra.html",
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )

@app.get("/contadores/pro")
async def freemiun(request: Request):
    return templates.TemplateResponse(
        "/components/contadores/pro_intermedia.html",
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )

@app.get("/contadores/senior")
async def freemiun(request: Request):
    return templates.TemplateResponse(
        "/components/contadores/senior_avanzada.html",
        {
            "request": request,
            "current_year": datetime.now().year
        }
    )

@app.get("/compare")
async def codigos_internos(request: Request):
   return templates.TemplateResponse("codigos_internos.html", {"request": request})


# **************** PLANTILLAS PARA MENÚs *************************
@app.get("/fast_menu_f2")
async def get_fast_menu(request: Request):
    
    return templates.TemplateResponse("dashboard/fast_menu_f2.html", {"request":request})   


# *********** RESUMEN DE QUERYs EMPRESA PARA CHATBOT DEMO **********************
@app.get("/api/resumen_empresa")
def resumen_empresa():
    session: Session = SessionLocal()
    
    # Obtener todas las empresas activas
    empresas = session.query(ChatClient).filter(ChatClient.status == "active").all()
    
    if not empresas:
        return {"error": "No hay empresas disponibles en la versión demo."}
    
    # Elegir una empresa aleatoria
    empresa = random.choice(empresas)

    datos_extra = [
        f"📌 Dirección: {empresa.address}",
        f"📞 Teléfono: {empresa.phone_number}",
        f"📧 Contacto: {empresa.contact_name} ({empresa.email})"
    ]
    
    resumen = random.sample(datos_extra, k=min(2, len(datos_extra)))  # Tomar 2 datos aleatorios

    session.close()

    # Sugerencias de preguntas más elaboradas
    sugerencias = [
        "📊 Los 5 productos más vendidos el mes pasado",
        "💰 Qué gastos representan el 80% del total",
        "📅 Qué impuestos se pagaron recientemente y en qué fecha",
        "📈 Cuál fue el ingreso total el último trimestre",
        "📉 Qué tipo de gasto ha aumentado más en el último año",
        "🔍 Qué clientes han generado más ingresos en los últimos 6 meses"
    ]
    random.shuffle(sugerencias)

    return {
        "empresa": empresa.business_name,
        "resumen": "<br>".join(resumen),
        "sugerencias": sugerencias[:3]  # Solo 3 sugerencias aleatorias
    }


# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(orgs.router, prefix="/api/orgs", tags=["Organizations"])# Cambio aquí para que coincida con el fetch
app.include_router(xero.router, prefix="/api", tags=["Xero Integration"])
app.include_router(htmx_views.router)
app.include_router(duilius.router)
app.include_router(chatbot_queries.router, prefix="/chatbot") #preguntas pre-definidas
app.include_router(loans.router,prefix="/api/loans", tags=["Loans"])
app.include_router(balance.router, prefix="/api", tags=["Balance Sheet"])
app.include_router(codigos_internos_xero.router, prefix="/api")
app.include_router(accounts.router, prefix="/api/accounts", tags=["Accounts"])
app.include_router(chat_generate_sql.router)
app.include_router(classifier_router)
app.include_router(chatbot_queries.router)
app.include_router(chatbot.router)
app.include_router(xero_balance_router, prefix="/auth", tags=["Xero Balance"])
#app.include_router(chatbot.router, prefix="/api")  # Usa un prefijo para organizar rutas

# En main.py agregar ruta para /api/sync
@app.get("/api/sync")
async def sync():
   return {"status": "success"}


# *********************** STRATEGY LINKEDIN *********************** STRATEGY LINKEDIN *********************** STRATEGY LINKEDIN *********************
@app.get("/linkedin")
async def linkedin(request: Request):
   return templates.TemplateResponse("strategy_linkedin.html", {"request": request})