from fastapi import APIRouter, Depends, Request, HTTPException, Response
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

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

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
async def oauth_callback(
    request: Request,
    code: str,
    db: Session = Depends(get_db)
):
    try:
        print(f"Received callback with code: {code}")  # Debug
        auth_result = await xero_auth_service.handle_oauth_callback(db, code)
        print(f"Auth result: {auth_result}")  # Debug
        
        # Log para debugging (opcional)
        print("Auth result:", auth_result)
        
        response = RedirectResponse(url="/auth/dashboard")
        response.set_cookie(
            key="session",
            value=auth_result["token"],
            httponly=True,
            secure=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax"
        )
        
        return response
        
    except Exception as e:
        print(f"Detailed error in callback: {str(e)}")  # Debug
        print(f"Exception type: {type(e)}")  # Debug
        import traceback
        print(f"Traceback: {traceback.format_exc()}")  # Debug
        raise HTTPException(
            status_code=400,
            detail=f"OAuth callback error: {str(e)}"
        )

@router.get("/dashboard")
async def dashboard(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session")
    session_data = xero_auth_service.decode_session_token(session_token)
    
    user_data = session_data["session_data"]["user_info"]
    organizations = session_data["session_data"]["organizations"]["connections"]
    last_sync = organizations[0]["last_sync"] if organizations else "Never"

    # Obtener token de la BD para la primera organización
    token = db.query(XeroToken).filter(
        XeroToken.tenant_id == organizations[0]["tenant_id"]
    ).first()

     # Asegurarnos que token_expires_at tenga timezone
    token_expiry = token.token_expires_at
    if token_expiry.tzinfo is None:
        token_expiry = token_expiry.replace(tzinfo=timezone.utc)

    if datetime.now(timezone.utc) >= token_expiry:
        print("Token expired, refreshing...")
        new_token = await xero_oauth_service.refresh_access_token(
            db=db,
            refresh_token=token.refresh_token
        )
        access_token = new_token["access_token"]
    else:
        access_token = token.access_token

    # Obtener chart of accounts con el token actualizado
    accounts = await get_chart_of_accounts(
        tenant_id=organizations[0]["tenant_id"], 
        access_token=access_token
    )

    print("Accounts response:", accounts)  # Debug

    context = {
        "request": request,
        "user": {
            "name": user_data["name"],
            "email": user_data["email"]
        },
        "last_sync": format_local_datetime(organizations[0]["last_sync"]),
        "last_sync": last_sync,
        "stats": {
            "org_count": len(organizations),
            "loan_count": 0,  # Por implementar
            "total_amount": 0  # Por implementar
        },
        "recent_loans": [],  # Por implementar
        "alerts": [],  # Por implementar
        "organizations": [
            {"id": org["tenant_id"], "name": org["name"]}
            for org in organizations
        ],
        "current_org_id": organizations[0]["tenant_id"] if organizations else None
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
    session = request.cookies.get("session")
    return {"authenticated": bool(session)}

@router.post("/refresh-token")
async def refresh_token(
    request: Request,
    db: Session = Depends(get_db)
):
    """Refresh Xero access token."""
    try:
        # Get current token from session
        session_token = request.cookies.get("session")
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
            key="session",
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