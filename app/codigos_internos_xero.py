import httpx
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.models.organization import Organization, OrganizationUser
from app.models.xero_token import XeroToken
from app.db.session import get_db
from app.services.xero_auth_service import XeroAuthService

def get_xero_auth_service():
    return XeroAuthService()

router = APIRouter()

async def get_xero_account_structure(
   tenant_id: str,
   access_token: str
) -> Dict:
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.xero.com/api.xro/2.0/Accounts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Xero-tenant-id": tenant_id,
                    "Accept": "application/json"
                }
            )
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text[:200]}...")  # Primeros 200 caracteres 

            if response.status_code == 401:
                        print("Token expired, needs refresh")
                        return None 

            if response.status_code == 200:
                return response.json()
            
            print(f"Error response: {response.text}")
            return None
    except Exception as e:
        print(f"Exception in get_xero_account_structure: {str(e)}")
        return None

@router.get("/codigos")
async def compare_accounts(
    request: Request,  # Agregar este parámetro
    db: Session = Depends(get_db),
    xero_auth_service: XeroAuthService = Depends(get_xero_auth_service)
):
    try:
        # Obtener user_id de la sesión
        session_token = request.cookies.get("session_xero")
        session_data = xero_auth_service.decode_session_token(session_token)
        user_id = session_data["session_xero"]["user_info"]["id"]
        
        # Modificar la consulta para filtrar por usuario
        organizations = (
            db.query(Organization, XeroToken)
            .join(XeroToken)
            .join(OrganizationUser)
            .filter(
                Organization.status == 'ACTIVE',
                OrganizationUser.user_id == user_id  # Filtrar por usuario
            )
            .all()
        )
        
        print(f"Organizations found for user {user_id}:", len(organizations))
        
        results = {}
        for org, token in organizations:
            print(f"Processing org: {org.name} with token: {token.tenant_id[:10]}...")
            accounts = await get_xero_account_structure(
                token.tenant_id,
                token.access_token
            )
            if accounts:
                results[org.name] = {
                    'tenant_id': token.tenant_id,
                    'accounts': accounts['Accounts']
                }
            else:
                print(f"No accounts found for {org.name}")

        print(f"Final results: {results}")
        return {"status": "success", "data": results}

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))