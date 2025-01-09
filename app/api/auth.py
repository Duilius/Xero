from fastapi import APIRouter, Depends, Request, HTTPException, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.services.xero_oauth import xero_oauth_service
from app.services.xero_auth_service import xero_auth_service
import secrets
from app.core.config import settings
from fastapi.templating import Jinja2Templates

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
    state: str,
    db: Session = Depends(get_db)
):
    """Handle OAuth callback from Xero."""
    # Verify state parameter
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or stored_state != state:
        raise HTTPException(status_code=400, detail="Invalid state parameter")

    try:
        # Handle OAuth callback and create session
        auth_result = await xero_auth_service.handle_oauth_callback(db, code)
        
        # Create response with redirect
        response = RedirectResponse(url="/dashboard")
        
        # Set session cookie
        response.set_cookie(
            key="session",
            value=auth_result["access_token"],
            httponly=True,
            secure=True,
            max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            samesite="lax"
        )
        
        # Remove state cookie
        response.delete_cookie("oauth_state")
        
        return response
        
    except Exception as e:
        # En caso de error, redirigir a login con mensaje
        return RedirectResponse(
            url=f"/auth/login?error={str(e)}",
            status_code=302
        )

@router.get("/dashboard")
async def dashboard(
    request: Request,
    db: Session = Depends(get_db)
):
    """Render dashboard page."""
    # Mock data for now - we'll replace with real data later
    context = {
        "request": request,
        "user": {
            "name": "John Doe",
            "email": "john@example.com"
        },
        "last_sync": "Today at 2:30 PM",
        "stats": {
            "org_count": 5,
            "loan_count": 12,
            "total_amount": 145000
        },
        "recent_loans": [
            {
                "from_org": "Company A",
                "to_org": "Company B",
                "amount": 50000,
                "status": "active",
                "date": "2024-01-06"
            },
            {
                "from_org": "Company C",
                "to_org": "Company D",
                "amount": 25000,
                "status": "pending",
                "date": "2024-01-05"
            }
        ],
        "alerts": [
            {
                "type": "warning",
                "title": "Loan Approval Required",
                "message": "New loan request from Company B needs your approval",
                "time": "1 hour ago"
            },
            {
                "type": "info",
                "title": "Sync Complete",
                "message": "Successfully synced data with Xero",
                "time": "2 hours ago"
            }
        ],
        "organizations": [  # Added for organization selector
            {"id": 1, "name": "Company A"},
            {"id": 2, "name": "Company B"},
            {"id": 3, "name": "Company C"}
        ],
        "current_org_id": 1  # Added for organization selector
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