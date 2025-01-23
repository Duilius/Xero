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
from app.models.organization import Organization, OrganizationUser

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
    
    # Obtener tenant_ids de la sesión actual
    tenant_ids = [
        org["tenant_id"] 
        for org in session_xero["session_xero"]["organizations"]["connections"]
    ]

    print(f"DEBUG - Tenant IDs from session: {tenant_ids}")
    
    # Obtener organizaciones con nombres reales
    org_data = (
        db.query(Organization, XeroToken)
        .join(OrganizationUser, Organization.id == OrganizationUser.organization_id)
        .join(XeroToken, Organization.id == XeroToken.organization_id)
        .filter(
            OrganizationUser.user_id == user_data["id"],
            XeroToken.tenant_id.in_(tenant_ids)
        )
        .all()
    )

    print(f"DEBUG - Organizations found: {[(org.name, token.tenant_id) for org, token in org_data]}")
    
    # Crear lista de organizaciones con nombres correctos
    orgs_data = [
        {
            "tenant_id": token.tenant_id,
            "name": org.name,  # Usar el nombre real de la organización
            "last_sync": token.last_sync_at.isoformat() if token.last_sync_at else None
        }
        for org, token in org_data
    ]

    print(f"DEBUG - Final orgs_data: {orgs_data}")
    
    # Actualizar la sesión con los nombres correctos
    new_session = {**session_xero}
    new_session["session_xero"]["organizations"] = {
        "connections": orgs_data
    }
    new_session_token = xero_auth_service.encode_session_token(new_session)
    
    context = {
        "request": request,
        "user": {
            "name": user_data["name"],
            "email": user_data["email"]
        },
        "organizations": orgs_data,
        "balance": {
            "assets": {"nonCurrent": [], "current": []},
            "liabilities": {"nonCurrent": [], "current": []},
            "equity": []
        }
    }
    
    # Crear respuesta con la sesión actualizada
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