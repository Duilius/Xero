from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse
from app.core.security import security_manager
from app.core.config import settings

class AuthMiddleware:
    def __init__(self):
        self.public_paths = {
            "/", 
            "/static", 
            "/auth/login",
            "/auth/connect/xero",
            "/auth/callback",
            "/auth/check-auth",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
    
    async def __call__(self, request: Request, call_next):
        path = request.url.path
        
        # Allow public paths
        if any(path.startswith(public_path) for public_path in self.public_paths):
            return await call_next(request)
        
        # Check for session cookie
        session_token = request.cookies.get("session")
        if not session_token:
            if request.headers.get("accept") == "application/json":
                raise HTTPException(status_code=401, detail="Not authenticated")
            return RedirectResponse(url="/auth/login")
        
        try:
            # Validate token and add user info to request state
            payload = security_manager.decode_token(session_token)
            request.state.user = payload
            request.state.user_id = int(payload["sub"])
            request.state.tenant_ids = payload.get("tenant_ids", [])
            
            response = await call_next(request)
            return response
            
        except HTTPException:
            response = RedirectResponse(url="/auth/login")
            response.delete_cookie("session")
            return response

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