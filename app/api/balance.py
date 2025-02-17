from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.xero_token import XeroToken
from app.services.xero_data_service import get_chart_of_accounts
from typing import List, Dict
import json
from app.services.xero_auth_service import XeroAuthService, xero_auth_service
from app.models.organization import Organization, OrganizationUser


def get_xero_auth_service():
    return XeroAuthService()

router = APIRouter()

@router.get("/organizations/list")
async def list_organizations(
    request: Request,
    db: Session = Depends(get_db),
    xero_auth_service: XeroAuthService = Depends(get_xero_auth_service)
):
    try:
        session_token = request.cookies.get("session_xero")
        session_data = xero_auth_service.decode_session_token(session_token)
        user_id = session_data["session_xero"]["user_info"]["id"]
        tenant_ids = [
            org["tenant_id"] 
            for org in session_data["session_xero"]["organizations"]["connections"]
        ]
        
        print(f"DEBUG - Processing tenant IDs: {tenant_ids}")
        
        # Consulta modificada para evitar duplicados
        organizations = (
            db.query(Organization, XeroToken)
            .join(OrganizationUser, Organization.id == OrganizationUser.organization_id)
            .join(XeroToken, Organization.id == XeroToken.organization_id)
            .filter(
                OrganizationUser.user_id == user_id,
                XeroToken.tenant_id.in_(tenant_ids)
            )
            .distinct(XeroToken.tenant_id)  # Agregar distinct por tenant_id
            .all()
        )

        print(f"DEBUG - Organizations found: {[(org.name, token.tenant_id, token.updated_at) for org, token in organizations]}")

        # Usar un diccionario para asegurar unicidad por tenant_id
        unique_orgs = {}
        for org, token in organizations:
            unique_orgs[token.tenant_id] = {
                "id": token.tenant_id,
                "name": org.name,
                "last_sync":token.updated_at
            }

        return {
            "organizations": list(unique_orgs.values())
        }
        
    except Exception as e:
        print(f"ERROR in list_organizations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/organizations/{tenant_id}")  # No incluir /api/ aquí porque ya está en el prefix
async def get_organization_data(tenant_id: str, db: Session = Depends(get_db)):
    try:
        print(f"Loading organization data for tenant_id: {tenant_id}")
        
        org_data = (
            db.query(Organization, XeroToken)
            .join(XeroToken)
            .filter(XeroToken.tenant_id == tenant_id)
            .first()
        )
        
        if not org_data:
            print(f"No data found for tenant_id: {tenant_id}")
            raise HTTPException(status_code=404, detail="Organization not found")
            
        org, token = org_data
        response_data = {
            "status": "success",
            "data": {
                "id": tenant_id,
                "name": org.name,
                "status": org.status,
                "last_sync": token.updated_at.isoformat() if token.updated_at else None
            }
        }
        print(f"Returning data: {response_data}")  # Debug
        return response_data
        
    except Exception as e:
        print(f"Error getting organization data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def process_balance_sheet(balance_data: Dict) -> Dict:
    """Procesa el balance sheet para extraer relaciones"""
    result = {
        "assets": {
            "nonCurrent": [],
            "current": []
        },
        "liabilities": {
            "nonCurrent": [],
            "current": []
        },
        "equity": []
    }

    if not balance_data or "Reports" not in balance_data:
        return result

    report = balance_data["Reports"][0]
    
    for section in report.get("Rows", []):
        if section.get("RowType") != "Section":
            continue

        section_title = section.get("Title", "").lower()
        
        # Procesar cada sección
        if "non-current assets" in section_title:
            result["assets"]["nonCurrent"] = process_section_rows(section.get("Rows", []))
        elif "current assets" in section_title:
            result["assets"]["current"] = process_section_rows(section.get("Rows", []))
        elif "non-current liabilities" in section_title:
            result["liabilities"]["nonCurrent"] = process_section_rows(section.get("Rows", []))
        elif "current liabilities" in section_title:
            result["liabilities"]["current"] = process_section_rows(section.get("Rows", []))
        elif "equity" in section_title:
            result["equity"] = process_section_rows(section.get("Rows", []))

    return result

def process_section_rows(rows: List[Dict]) -> List[Dict]:
    """Procesa las filas de una sección del balance"""
    items = []
    for row in rows:
        if row.get("RowType") != "Row":
            continue

        cells = row.get("Cells", [])
        if len(cells) < 2:
            continue

        try:
            name = cells[0].get("Value", "")
            # Buscar nombres de organizaciones en el valor
            if any(keyword in name.lower() for keyword in ["loan", "investment", "share"]):
                amount = float(cells[1].get("Value", "0").replace(",", ""))
                items.append({
                    "id": cells[0].get("Attributes", [{}])[0].get("Value"),  # Account ID
                    "org": name,
                    "amount": amount
                })
        except (ValueError, IndexError):
            continue

    return items


@router.get("/organizations/list")
async def list_organizations(request: Request,db: Session = Depends(get_db)):
    """Listar organizaciones conectadas del usuario actual"""
    try:
        # Obtener datos de la sesión directamente
        session_token = request.cookies.get("session_xero")
        session_data = xero_auth_service.decode_session_token(session_token)
        tenant_ids = [
            org["tenant_id"] 
            for org in session_data["session_xero"]["organizations"]["connections"]
        ]
        
        fechas = [
            org["last_sync"] 
            for org in session_data["session_xero"]["organizations"]["connections"]
        ]
        print(f"FECHAS 🙋‍♂️🙋‍♂️😀 - SYNC: {fechas}")
        print(f"DEBUG - Tenant IDs: {tenant_ids}")
        
        orgs = db.query(XeroToken).filter(
            XeroToken.tenant_id.in_(tenant_ids)
        ).all()
        
    except Exception as e:
        print(f"ERROR in list_organizations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))