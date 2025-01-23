from typing import Optional
from fastapi import Request, HTTPException
from fastapi.responses import RedirectResponse, JSONResponse
from app.core.security import security_manager
from app.core.config import settings
from app.services.xero_auth_service import XeroAuthService
from datetime import datetime, timezone

class AuthMiddleware:
   def __init__(self):
       self.public_paths = {"/", "/static", "/auth/login", "/auth/connect/xero", 
                          "/auth/callback", "/auth/check-auth", "/docs", "/redoc", 
                          "/openapi.json"}
       self.xero_auth_service = XeroAuthService()

   async def __call__(self, request: Request, call_next):
       path = request.url.path
       
       # Verificar rutas públicas
       if any(path.startswith(public) for public in self.public_paths):
           return await call_next(request)
       
       try:
           # Verificar sesión
           session_token = request.cookies.get("session_xero")
           if not session_token:
               print("DEBUG - No session token found")
               return RedirectResponse("/auth/login")

           # Decodificar y verificar token
           try:
               session_data = self.xero_auth_service.decode_session_token(session_token)
               print("DEBUG - Session data:", session_data)  # Ver qué datos tenemos
               
               # Verificar si el token de Xero necesita refresh
               if session_data.get("session_xero"):
                   for org in session_data["session_xero"]["organizations"]["connections"]:
                       tenant_id = org["tenant_id"]
                       try:
                           # Verificar y refrescar token si es necesario
                           await self.xero_auth_service.refresh_access_token(
                               tenant_id=tenant_id,
                               organization_id=None  # Temporal hasta actualizar función
                           )
                       except Exception as e:
                           print(f"DEBUG - Error refreshing token for {tenant_id}: {e}")
               
               # Establecer datos en request.state
               request.state.user_id = session_data["sub"]
               request.state.tenant_ids = session_data["session_xero"]["organizations"]["connections"]
               print("DEBUG - Set tenant_ids:", request.state.tenant_ids)
               
               response = await call_next(request)
               return response
               
           except Exception as e:
               print(f"DEBUG - Session validation error: {str(e)}")
               response = RedirectResponse("/auth/login", status_code=303)
               response.delete_cookie("session_xero")
               return response

       except Exception as e:
           print(f"DEBUG - Auth middleware error: {str(e)}")
           return RedirectResponse("/auth/login", status_code=303)
       

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