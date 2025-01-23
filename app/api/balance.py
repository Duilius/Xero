from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.xero_token import XeroToken
from app.services.xero_data_service import get_chart_of_accounts
from typing import List, Dict
import json
from app.services.xero_auth_service import XeroAuthService
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

        print(f"DEBUG - Organizations found: {[(org.name, token.tenant_id) for org, token in organizations]}")

        # Usar un diccionario para asegurar unicidad por tenant_id
        unique_orgs = {}
        for org, token in organizations:
            unique_orgs[token.tenant_id] = {
                "id": token.tenant_id,
                "name": org.name
            }

        return {
            "organizations": list(unique_orgs.values())
        }
        
    except Exception as e:
        print(f"ERROR in list_organizations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/organizations/{org_id}/balance")
async def get_organization_balance(
    org_id: str,
    db: Session = Depends(get_db)
):
    """Obtener balance sheet de una organización"""
    try:
        token = db.query(XeroToken).filter(
            XeroToken.tenant_id == org_id
        ).first()
        
        if not token:
            raise HTTPException(status_code=404, detail="Organization not found")

        balance_data = await get_chart_of_accounts(
            tenant_id=org_id,
            access_token=token.access_token
        )

        # Procesar el balance para extraer relaciones
        return process_balance_sheet(balance_data)

    except Exception as e:
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
        
        print(f"DEBUG - Tenant IDs: {tenant_ids}")
        
        orgs = db.query(XeroToken).filter(
            XeroToken.tenant_id.in_(tenant_ids)
        ).all()
        
    except Exception as e:
        print(f"ERROR in list_organizations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))