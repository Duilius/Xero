#endpoints que manejarán las solicitudes HTMX  <<====== endpoints que manejarán las solicitudes HTMX <<====

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session
from fastapi.responses import HTMLResponse, JSONResponse, Response
from app.db.session import get_db
from app.core.middlewares import get_current_user_id
from app.services.adjustment_service import adjustment_service
from app.services.xero_data_service import get_chart_of_accounts
from app.models.xero_token import XeroToken
from app.models.user import User
from fastapi.templating import Jinja2Templates
from app.core import security
from typing import Optional, Dict
from app.services.xero_auth_service import xero_auth_service  # Instancia del servicio

router = APIRouter(prefix="/adjustments")
templates = Jinja2Templates(directory="app/templates")

@router.get("/modal/{org_id}", response_class=HTMLResponse)
async def get_adjustment_modal(
    request: Request,
    org_id: int,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
):
    """Renderiza el modal de ajustes."""
    user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse(
        "components/adjustment_modal.html",
        {"request": request, "org_id": org_id, "user": user}
    )

@router.get("/compare/{org_id}")
async def get_comparison_data(
    request: Request,
    org_id: str,
    db: Session = Depends(get_db),
    user_id: int = Depends(get_current_user_id)
) ->Response:
    """Obtiene y muestra los datos comparativos."""
    try:
        print(f"Comparing data for org_id: {org_id}")
        
        # Obtener token de sesión para acceder a los tenant_ids
        session_token = request.cookies.get("session")
        payload = xero_auth_service.decode_session_token(session_token)
        
        # Obtener las organizaciones del payload
        tenant_ids = payload.get('tenant_ids', [])
        if org_id not in tenant_ids:
            raise HTTPException(status_code=400, detail="Organization not authorized")
        
        # Obtener datos de comparación usando los tenant_ids directamente
        comparison_data = await adjustment_service.get_comparison_data(
            db,
            tenant_ids[0],  # Primera organización (la seleccionada)
            org_id         # Segunda organización (la que se va a comparar)
        )
        
        return templates.TemplateResponse(
            "components/comparison_data.html",
            {
                "request": request,
                "org_1": comparison_data["org_1"],
                "org_2": comparison_data["org_2"],
                "discrepancy": comparison_data["discrepancy"]
            }
        )
    except Exception as e:
        print(f"Error in comparison: {str(e)}")
        return JSONResponse(
            status_code=422,
            content={"detail": str(e)}
        )

@router.get("/request-form", response_class=HTMLResponse)
async def get_request_form(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id)
):
    """Renderiza el formulario de solicitud de ajuste."""
    authorizers = await adjustment_service.get_org_authorizers(
        db, 
        current_user.organization_id
    )
    
    return templates.TemplateResponse(
        "components/adjustment_form.html",
        {
            "request": request,
            "authorizers": authorizers
        }
    )