from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from app.core.security import security_manager
from app.core.config import settings

class AuthMiddleware:
    def __init__(self):
        self.public_paths = {"/", "/static", "/auth/login", "/auth/connect/xero", 
                           "/auth/callback", "/auth/check-auth", "/docs", "/redoc", 
                           "/openapi.json"}
    
    async def __call__(self, request: Request, call_next):
        path = request.url.path
        
        # Public paths
        if path in self.public_paths or path.startswith("/static/"):
            return await call_next(request)
            
        # Protected paths
        session_token = request.cookies.get("session")
        if not session_token:
            return RedirectResponse(url="/auth/login")
            
        try:
            payload = security_manager.decode_token(session_token)
            request.state.user_id = int(payload["sub"])  # Convertir de vuelta a int
            request.state.tenant_ids = payload.get("tenant_ids", [])
            return await call_next(request)
        except Exception as e:
            print(f"Auth error: {str(e)}")  # Debug
            return RedirectResponse(url="/auth/login")

async def get_current_user_id(request: Request) -> int:
    """Dependency to get current user ID."""
    if not hasattr(request.state, "user_id"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.state.user_id

async def get_current_tenant_ids(request: Request) -> list[str]:
    """Dependency to get current user's tenant IDs."""
    if not hasattr(request.state, "tenant_ids"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return request.state.tenant_ids