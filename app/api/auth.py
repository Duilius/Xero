from fastapi import FastAPI, APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
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

app = FastAPI()
# Static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")
xero_client = XeroClient()  # Instancia del cliente



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
    session_xero = xero_auth_service.decode_session_token(session_token)
    
    user_data = session_xero["session_xero"]["user_info"]
    organizations = session_xero["session_xero"]["organizations"]["connections"]
    
    # Obtener préstamos para cada organización
    loans_data = []
    total_amount = 0
    for org in organizations:
        token = db.query(XeroToken).filter(
            XeroToken.tenant_id == org["tenant_id"]
        ).first()
        if token:
            # Obtener datos de la cuenta de préstamos
            accounts = await get_chart_of_accounts(
                tenant_id=org["tenant_id"], 
                access_token=token.access_token
            )
            if accounts and "Reports" in accounts:
                report = accounts["Reports"][0]
                for row in report.get("Rows", []):
                    if (row.get("RowType") == "Section" and 
                        row.get("Title", "").lower() == "non-current liabilities"):
                        
                        # Procesar las filas de esta sección
                        for subrow in row.get("Rows", []):
                            # Buscar filas que contengan 'Loan' en el título
                            if (subrow.get("RowType") == "Row" and 
                                "Loan" in subrow.get("Cells", [])[0].get("Value", "")):
                                
                                cells = subrow.get("Cells", [])
                                if len(cells) >= 2:
                                    try:
                                        # El Value de la segunda celda contiene el balance
                                        balance = float(cells[1].get("Value", "0").replace(",", ""))
                                        loan_name = cells[0].get("Value", "")
                                        
                                        if balance < 0:
                                            loans_data.append({
                                                "from_org": org["name"],
                                                "to_org": loan_name.replace("Loan to ", "").replace("Loan-1 to ", ""),
                                                "amount": abs(balance),
                                                "status": "active" if balance < 0 else "pending",
                                                "date": report.get("ReportDate"),
                                                "from_org_id": org["tenant_id"],
                                                # Agregar to_org_id buscando en organizations
                                                "to_org_id": next(
                                                    (org["tenant_id"] 
                                                    for org in organizations 
                                                    if org["name"] in loan_name),
                                                    None
                                                )
                                            })
                                            total_amount += abs(balance)
                                    except (ValueError, TypeError) as e:
                                        print(f"Error processing balance for {loan_name}: {e}")

    context = {
        "request": request,
        "user": {
            "name": user_data["name"],
            "email": user_data["email"]
        },
        "last_sync": organizations[0]["last_sync"] if organizations else "Never",
        "stats": {
            "org_count": len(organizations),
            "loan_count": len(loans_data),
            "total_amount": total_amount
        },
        "recent_loans": loans_data[:5],  # Mostrar solo los 5 más recientes
        "organizations": [
            {"id": org["tenant_id"], "name": org["name"]}
            for org in organizations
        ],
        "current_org_id": None  # Se actualizará cuando se seleccione una org
    }
    
    return templates.TemplateResponse("dashboard/index.html", context)

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