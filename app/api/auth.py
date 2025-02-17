from fastapi import FastAPI, APIRouter, Depends, Request, HTTPException, Response, Query
from fastapi.responses import RedirectResponse, HTMLResponse
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.xero_oauth_service import xero_oauth_service
from app.services.xero_auth_service import xero_auth_service
import secrets
from app.core.config import settings
from fastapi.templating import Jinja2Templates
import logging
from app.services.xero_data_service import get_chart_of_accounts
from app.models.xero_token import XeroToken
from datetime import datetime, timezone
from app.utils.date_utils import format_local_datetime
from app.core.middlewares import get_current_user_id
from app.models.organization import Organization, OrganizationUser
from app.services.xero_client import XeroClient
from fastapi.staticfiles import StaticFiles
from app.services.xero_auth_service import XeroAuthService
from app.models.account_structures import XeroAccountStructure
from app.codigos_internos_xero import get_xero_account_structure
from pathlib import Path
from app.models.xero_mapping import AccountMapping
from app.core.services.xero_balance_service   import  xero_balance_service
from app.core.services.xero_service import xero_service
#from app.core.services.xero_auth_service import xero_auth_service
from app.services.xero_auth_service import xero_auth_service
import httpx

app = FastAPI()
# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
xero_client = XeroClient()  # Instancia del cliente

def get_xero_auth_service():
    return XeroAuthService()

# Add custom filters
def format_number(value):
    """Format number with thousands separator and 2 decimal places."""
    try:
        return "{:,.2f}".format(float(value))
    except (ValueError, TypeError):
        return value

templates.env.filters["format_number"] = format_number

@router.get("/login")
async def login_page(request: Request):
    """Render login page."""
    return templates.TemplateResponse(
        "auth/login.html",
        {"request": request}
    )

@router.get("/connect/xero")
async def connect_xero(response: Response):
    """Initiate Xero OAuth flow."""
    # Generate state parameter to prevent CSRF
    state = secrets.token_urlsafe(32)
    authorization_url = xero_oauth_service.get_authorization_url(state)
    
    # Set state cookie
    response = RedirectResponse(url=authorization_url)
    response.set_cookie(
        key="oauth_state",
        value=state,
        httponly=True,
        secure=True,
        max_age=3600,
        samesite="lax"
    )
    
    return response

@router.get("/callback")
async def oauth_callback(request: Request, code: str, db: Session = Depends(get_db)):
   auth_result = await xero_auth_service.handle_oauth_callback(db, code)
   print("Token to be set in cookie:", auth_result["token"][:20] + "...")
   response = RedirectResponse(url="/auth/dashboard")
   
   response.set_cookie(
       key="session_xero",
       value=auth_result["token"],
       httponly=False,  # Temporalmente false para debug
       secure=False,    # Temporalmente false para debug
       path="/",
       max_age=60 * 60
   )
   
   print("Cookie set. Response headers:", response.headers)
   return response

@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session_xero")
    #session_xero = XeroAuthService.decode_session_token(session_token)
    session_xero = xero_auth_service.decode_session_token(session_token)
    
    user_data = session_xero["session_xero"]["user_info"]
    tenant_ids = [org["tenant_id"] for org in session_xero["session_xero"]["organizations"]["connections"]]

    # Obtener organizaciones y sus datos fiscales
    org_data = (
        db.query(Organization, XeroToken)
        .join(OrganizationUser)
        .join(XeroToken)
        .filter(
            OrganizationUser.user_id == user_data["id"],
            XeroToken.tenant_id.in_(tenant_ids)
        )
        .all()
    )

    # Obtener datos fiscales de Xero
    orgs_data = []
    for org, token in org_data:
        org_details = await xero_service.get_organization_details(token.access_token, token.tenant_id)
        org_info = {
            "tenant_id": token.tenant_id,
            "name": org.name,
            "last_sync": token.updated_at.isoformat() if token.updated_at else None,
            "currency": org_details.get("BaseCurrency"),
            "fy_end_day": org_details.get("FinancialYearEndDay"),
            "fy_end_month": org_details.get("FinancialYearEndMonth")
        }
        orgs_data.append(org_info)

    new_session = {**session_xero}
    new_session["session_xero"]["organizations"] = {"connections": orgs_data}
    new_session_token = xero_auth_service.encode_session_token(new_session)

    context = {
        "request": request,
        "user": {"name": user_data["name"], "email": user_data["email"]},
        "organizations": orgs_data,
        "balance": {
            "assets": {"nonCurrent": [], "current": []},
            "liabilities": {"nonCurrent": [], "current": []},
            "equity": []
        }
    }

    response = templates.TemplateResponse("dashboard/index-20Ene.html", context)
    response.set_cookie("session_xero", new_session_token)
    return response

@router.post("/logout")
async def logout(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle user logout."""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie("session")
    response.delete_cookie("oauth_state")
    
    return response

@router.get("/check-auth")
async def check_auth(request: Request):
    """Check if user is authenticated."""
    session = request.cookies.get("session_xero")
    return {"authenticated": bool(session)}

@router.post("/refresh-token")
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh Xero access token."""
    try:
        # Get current token from session
        session_token = request.cookies.get("session_xero")
        if not session_token:
            raise HTTPException(status_code=401, detail="No session found")

        # Get user info from session token
        #user_info = XeroAuthService.decode_session_token(session_token)
        user_info = xero_auth_service.decode_session_token(session_token)
        
        # Refresh token
        new_token = await xero_oauth_service.refresh_access_token(
            db, 
            user_info["user_id"]
        )
        
        # Create response with new token
        response = Response()
        response.set_cookie(
            key="session_xero",
            value=new_token,
            httponly=True,
            secure=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax"
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/permissions")
async def permissions_page(request: Request):
    """Muestra la página de explicación de permisos."""
    permissions = xero_oauth_service.get_permissions_description()
    return templates.TemplateResponse(
        "auth/permissions.html",
        {
            "request": request,
            "permissions": permissions
        }
    )


# ***************************  Búsqueda de Cuentas (y su código)   ************************************
""" Buscamos Código de Cuenta y account_id [ código de Xero para códigos de cuenta]"""
@router.get("/auth/codigo", response_class=HTMLResponse)
def search_accounts(
    q: str = Query(..., min_length=3),
    lender_org_id: str = Query(None),  # Para prestamista
    borrower_org_id: str = Query(None),  # Para prestatario
    db: Session = Depends(get_db)
):
    print("🔍 Búsqueda con:", {
        "query": q,
        "lender_org": lender_org_id,
        "borrower_org": borrower_org_id
    })
    
    try:
        # Determinar qué organización está buscando
        org_id = lender_org_id or borrower_org_id
        is_lender = bool(lender_org_id)
        
        results = db.query(AccountMapping)\
            .with_entities(
                AccountMapping.account_code, 
                AccountMapping.account_name
            )\
            .filter(
                AccountMapping.organization_id == org_id,
                or_(
                    AccountMapping.account_code.ilike(f"%{q}%"),
                    AccountMapping.account_name.ilike(f"%{q}%")
                )
            )\
            .distinct(AccountMapping.account_code, AccountMapping.account_name)\
            .limit(20)\
            .all()

        print("✅ Cuentas encontradas:", len(results))

        if not results:
            return """<p class='text-gray-500 p-2 text-center'>No se encontraron cuentas</p>"""
        
        # Construir HTML con los resultados
        html_content = ""
        for account in results:
            html_content += f"""
                <div class="account-row p-3 border-b hover:bg-gray-50 dark:hover:bg-gray-700 cursor-pointer"
                     onclick="selectAccount('{account.account_code}', '{account.account_name}', {'true' if is_lender else 'false'})"
                     _="on click add .selected to me
                        then remove .selected from .account-row where not me">
                    <div class="flex justify-between items-center">
                        <span class="font-medium text-gray-700 dark:text-gray-300">{account.account_code}</span>
                        <span class="text-gray-600 dark:text-gray-400">{account.account_name}</span>
                    </div>
                </div>
            """
        
        return html_content
        
    except Exception as e:
        print("❌ Error en búsqueda:", e)
        return """<p class='text-red-500 p-2 text-center'>Error en la búsqueda</p>"""


#****************  CON HTMX EN FROMTEND ************  CON HTMX EN FROMTEND ************  CON HTMX EN FROMTEND ************

@router.get("/accounts/{org_id}")
async def get_organization_accounts(org_id: str, request: Request, db: Session = Depends(get_db)):
    print(f"🔍 Buscando cuentas para organización slug: {org_id}")
    
    try:
        # Primero obtener el id real de la organización
        org = db.query(Organization).filter(Organization.slug == org_id).first()
        if not org:
            raise HTTPException(404, "Organización no encontrada")

        accounts = db.query(AccountMapping).filter(
            AccountMapping.organization_id == org.id  # Usar el ID numérico
        ).with_entities(
            AccountMapping.account_code.label('code'),
            AccountMapping.account_name.label('name'),
            AccountMapping.account_type.label('type')
        ).order_by(AccountMapping.account_code).all()
        
        print(f"✅ Encontradas {len(accounts)} cuentas")
        return [{"code": a.code, "name": a.name, "type": a.type} for a in accounts]
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise HTTPException(500, str(e))

#********************           **************************                 ************************           ***************


@router.get("/auth/accounts/search")
async def search_accounts(
   request: Request,
   q: str = Query(..., min_length=3),
   org_id: str = Query(...),
   db: Session = Depends(get_db)
):
   print(f"🔍 Buscando cuentas para org_id: {org_id}, query: {q}")
   
   try:
       # Buscar cuentas que coincidan
       accounts = db.query(AccountMapping).filter(
           AccountMapping.organization_id == org_id,
           or_(
               AccountMapping.account_code.ilike(f"%{q}%"),
               AccountMapping.account_name.ilike(f"%{q}%")
           )
       ).all()
       
       print(f"✅ Encontradas {len(accounts)} cuentas")
       
       # Devolver HTML formateado
       html_content = ""
       for account in accounts:
           html_content += f"""
               <div class="account-row p-3 border-b border-gray-200 hover:bg-gray-50 cursor-pointer
                           text-gray-700 dark:text-gray-200 dark:hover:bg-gray-700"
                    hx-get="/auth/accounts/select/{org_id}/{account.account_code}"
                    hx-target="#selected-account-{org_id}"
                    _="on click remove .selected from .account-row
                       then add .selected to me">
                   <div class="flex justify-between items-center">
                       <span class="font-medium">{account.account_code}</span>
                       <span>{account.account_name}</span>
                   </div>
               </div>
           """
       
       return HTMLResponse(content=html_content if accounts else """
           <div class="p-3 text-gray-500 dark:text-gray-400 text-center">
               No se encontraron cuentas
           </div>
       """)
       
   except Exception as e:
       print(f"❌ Error buscando cuentas: {e}")
       return HTMLResponse(
           content="""
               <div class="p-3 text-red-500 dark:text-red-400 text-center">
                   Error al buscar cuentas
               </div>
           """,
           status_code=500
       )

#******* MANEJO DE LA SELECCIÓN DE UNA CUENTA ****************** MANEJO DE LA SELECCIÓN DE UNA CUENTA******* MANEJO DE LA SELECCIÓN DE UNA CUENTA
@router.get("/auth/accounts/select/{org_id}/{account_code}")
async def select_account(
   org_id: str,
   account_code: str,
   request: Request,
   db: Session = Depends(get_db)
):
   print(f"🎯 Seleccionando cuenta {account_code} para org {org_id}")
   
   try:
       # Buscar la cuenta
       account = db.query(AccountMapping).filter(
           AccountMapping.organization_id == org_id,
           AccountMapping.account_code == account_code
       ).first()
       
       if not account:
           return HTMLResponse(
               content="""
                   <div class="text-red-500 dark:text-red-400">
                       Cuenta no encontrada
                   </div>
               """,
               status_code=404
           )
       
       # Devolver HTML con la cuenta seleccionada
       return HTMLResponse(f"""
           <div class="selected-account p-2 bg-blue-50 dark:bg-blue-900 rounded-lg
                       border border-blue-200 dark:border-blue-700">
               <div class="flex justify-between items-center">
                   <span class="font-medium text-blue-700 dark:text-blue-300">
                       {account.account_code}
                   </span>
                   <span class="text-blue-600 dark:text-blue-400">
                       {account.account_name}
                   </span>
               </div>
               <input type="hidden" 
                      name="selected_account_{org_id}" 
                      value="{account.account_code}"
                      hx-trigger="change"
                      hx-post="/auth/accounts/validate-selection"
                      hx-include="[name^='selected_account_']">
           </div>
       """)
       
   except Exception as e:
       print(f"❌ Error seleccionando cuenta: {e}")
       return HTMLResponse(
           content="""
               <div class="text-red-500 dark:text-red-400 text-center">
                   Error al seleccionar cuenta
               </div>
           """,
           status_code=500
       )


#************ VEROFOCAR QUE AMBAS CUENTAS ESTEÉN SELECCIONADAS ************ VEROFOCAR QUE AMBAS CUENTAS ESTEÉN SELECCIONADAS 
@router.post("/auth/accounts/validate-selection")
async def validate_account_selection(
   request: Request,
   db: Session = Depends(get_db)
):
   print("🔍 Validando selección de cuentas")
   
   try:
       # Obtener datos del form
       form = await request.form()
       lender_account = form.get("selected_account_lender")
       borrower_account = form.get("selected_account_borrower")
       
       print(f"📋 Cuentas seleccionadas - Prestamista: {lender_account}, Prestataria: {borrower_account}")

       if not lender_account or not borrower_account:
           return HTMLResponse("""
               <button id="processButton" 
                       class="w-full px-4 py-2 bg-gray-400 text-white rounded-lg cursor-not-allowed"
                       disabled>
                   Seleccione ambas cuentas
               </button>
           """)

       # Validar que las cuentas existan
       lender = db.query(AccountMapping).filter(
           AccountMapping.account_code == lender_account
       ).first()
       
       borrower = db.query(AccountMapping).filter(
           AccountMapping.account_code == borrower_account
       ).first()

       if not lender or not borrower:
           return HTMLResponse("""
               <button id="processButton" 
                       class="w-full px-4 py-2 bg-red-500 text-white rounded-lg cursor-not-allowed"
                       disabled>
                   Error: Cuenta(s) no válida(s)
               </button>
           """)

       # Todo válido, habilitar el botón
       return HTMLResponse("""
           <button id="processButton" 
                   class="w-full px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg
                          transition-colors duration-200"
                   hx-get="/auth/process-balances"
                   hx-include="[name^='selected_account_']"
                   hx-target="#results-container">
               Procesar Saldos
           </button>
       """)

   except Exception as e:
       print(f"❌ Error en validación: {e}")
       return HTMLResponse("""
           <button id="processButton" 
                   class="w-full px-4 py-2 bg-red-500 text-white rounded-lg cursor-not-allowed"
                   disabled>
               Error en validación
           </button>
       """, status_code=500)

# ************ PROCESAMIENTO DE SALDOS  ************ PROCESAMIENTO DE SALDOS  ************ PROCESAMIENTO DE SALDOS 
@router.get("/auth/process-balances")
async def process_balances(
   request: Request,
   db: Session = Depends(get_db)
):
   print("🔄 Iniciando procesamiento de saldos")
   
   try:
       # Obtener datos necesarios
       form = await request.form()
       lender_account = form.get("selected_account_lender")
       borrower_account = form.get("selected_account_borrower")
       
       # Obtener token de sesión
       session_token = request.cookies.get("session_xero")
       session_data = xero_auth_service.decode_session_token(session_token)
       access_token = session_data["session_xero"]["token"]["access_token"]

       print(f"📊 Procesando saldos para cuentas: {lender_account} y {borrower_account}")

       # Obtener saldos de Xero
       async with httpx.AsyncClient() as client:
           # Saldo prestamista
           lender_balance = await get_account_balance(
               client, 
               access_token,
               lender_account
           )
           
           # Saldo prestatario
           borrower_balance = await get_account_balance(
               client, 
               access_token,
               borrower_account
           )

       return HTMLResponse(f"""
           <div class="space-y-4 p-4 bg-white dark:bg-gray-800 rounded-lg shadow">
               <div class="flex justify-between items-center p-3 bg-blue-50 dark:bg-blue-900 rounded">
                   <span class="font-medium">Cuenta Prestamista ({lender_account})</span>
                   <span class="text-blue-600 dark:text-blue-300">{format_currency(lender_balance)}</span>
               </div>
               
               <div class="flex justify-between items-center p-3 bg-red-50 dark:bg-red-900 rounded">
                   <span class="font-medium">Cuenta Prestataria ({borrower_account})</span>
                   <span class="text-red-600 dark:text-red-300">{format_currency(borrower_balance)}</span>
               </div>
               
               <div class="mt-4 p-3 bg-gray-50 dark:bg-gray-700 rounded">
                   <div class="flex justify-between items-center">
                       <span class="font-bold">Diferencia</span>
                       <span class="font-bold {get_difference_color(lender_balance, borrower_balance)}">
                           {format_currency(lender_balance - borrower_balance)}
                       </span>
                   </div>
               </div>
           </div>
       """)

   except Exception as e:
       print(f"❌ Error procesando saldos: {e}")
       return HTMLResponse("""
           <div class="p-4 bg-red-100 dark:bg-red-900 text-red-700 dark:text-red-300 rounded-lg">
               Error al procesar saldos. Por favor, intente nuevamente.
           </div>
       """, status_code=500)

async def get_account_balance(client, access_token, account_code):
   # Implementar llamada a Xero API para obtener balance
   # Retornar el balance como float
   pass

def format_currency(amount):
   return f"${amount:,.2f}"

def get_difference_color(lender, borrower):
   diff = lender - borrower
   if abs(diff) < 0.01:  # Prácticamente iguales
       return "text-green-600 dark:text-green-400"
   return "text-yellow-600 dark:text-yellow-400"


# ********************
@router.get("/accounts/plan/{org_id}")
async def get_account_plan(
    org_id: str,
    request: Request,
    db: Session = Depends(get_db)
):
    print(f"🤶🎅Received request for org_id: {org_id}")  # Debug
    try:
        # Obtener y refrescar token si es necesario
        token = db.query(XeroToken).filter(
            XeroToken.organization_id == org_id
        ).first()
        
        token = await xero_auth_service.refresh_token_if_needed(token, db)


        # Obtener token de sesión
        session_token = request.cookies.get("session_xero")
        session_xero = xero_auth_service.decode_session_token(session_token)
        
        # Buscar el plan contable en la base de datos
        accounts = db.query(AccountMapping).filter(
            AccountMapping.organization_id == org_id
        ).with_entities(
            AccountMapping.account_code,
            AccountMapping.account_name,
            AccountMapping.account_type
        ).order_by(AccountMapping.account_code).all()
        
        # Formatear la respuesta
        account_plan = {
            "organization_id": org_id,
            "last_sync": session_xero["session_xero"]["organizations"]["connections"][0]["last_sync"],
            "accounts": [
                {
                    "code": account.account_code,
                    "name": account.account_name,
                    "type": account.account_type
                }
                for account in accounts
            ]
        }
        
        return account_plan
        
    except Exception as e:
        print(f"Error loading account plan: {e}")  # Debug
        raise HTTPException(
            status_code=500,
            detail=f"Error loading account plan: {str(e)}"
        )


# ********************** ENDPOINT PARA "CUADRO COMBINADO"  ***********************************
# En app/api/balance.py o donde esté el endpoint actual
@router.get("/api/organizations/{tenant_id}")
async def get_organization_data(
    tenant_id: str,
    from_date: str = Query(default=None),  # Especificar default
    to_date: str = Query(default=None),    # Especificar default
    account_id: str = Query(default=None), # Especificar default
    db: Session = Depends(get_db),
    xero_auth_service: XeroAuthService = Depends(get_xero_auth_service)
):
    try:
        # Obtener token
        token = db.query(XeroToken).filter(
            XeroToken.tenant_id == tenant_id
        ).first()

        if not token:
            raise HTTPException(status_code=404, detail="Organization not found")
        
        # Obtener estructura de cuentas si no se especifica account_id
        if not account_id:
            accounts = await get_xero_account_structure(
                tenant_id=token.tenant_id,
                access_token=token.access_token
            )
            return {
                "organization_id": tenant_id,
                "accounts": accounts["Accounts"] if accounts else []
            }
        
        # Si hay account_id, obtener balance específico
        if from_date and to_date:
            # Aquí implementaremos la obtención del balance por período
            pass

        return {
            "organization_id": tenant_id,
            "account_id": account_id,
            "accounts": []  # Por ahora retornamos lista vacía
        }

    except Exception as e:
        print(f"Error getting organization data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


#******************************* NUEVO ENDPOINT PARA BUSCAR SALDOS ENTRE ORGANIZACIONES *********************************
# En auth.py
@router.get("/balances/{from_org_id}/{to_org_id}")
async def get_balance(
    from_org_id: str,
    to_org_id: str,
    start_date: str,
    end_date: str,
    request: Request,
    db: Session = Depends(get_db)
):
    try:
        session_token = request.cookies.get("session_xero")
        session_xero = xero_auth_service.decode_session_token(session_token)

        print("===>Session_Xero ===>", session_xero)
        
        # Obtener token de DB y refrescarlo si es necesario
        token = db.query(XeroToken).filter_by(tenant_id=from_org_id).first()

        print("===>el TOKEN ===> ", token)
        print("===>el ACCESS TOKEN ===> ", token.access_token)

        token = await xero_auth_service.refresh_token_if_needed(token, db)
        
        print("===>TOKEN REFRESCADO ===> ", token)
        balance =   await xero_balance_service.get_balance_between_orgs(
            token.access_token,
            from_org_id,
            to_org_id,
            start_date,
            end_date
        )

        print("==> EL BALANCE ===> ", balance)
        return {"balance": balance}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
