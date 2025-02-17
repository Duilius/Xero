# app/services/xero_account_service.py
import httpx
from typing import List
from sqlalchemy.orm import Session
from app.models.account_structures import XeroAccountStructure
from datetime import datetime

async def sync_account_structure(
    db: Session,
    org_id: int,
    tenant_id: str,
    access_token: str
) -> List[XeroAccountStructure]:
    try:
        # Obtener cuentas de Xero
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.xero.com/api.xro/2.0/Accounts",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Xero-tenant-id": tenant_id,
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 200:
                accounts_data = response.json()
                
                # Procesar cada cuenta
                for account in accounts_data.get("Accounts", []):
                    account_structure = XeroAccountStructure(
                        organization_id=org_id,
                        account_id=account["AccountID"],
                        code=account["Code"],
                        name=account["Name"],
                        type=account["Type"],
                        report_type="BS" if account["Type"] in ["ASSET", "LIABILITY", "EQUITY"] else "PL",
                        last_sync=datetime.utcnow()
                    )
                    db.add(account_structure)
                
                db.commit()
                print(f"Synchronized {len(accounts_data.get('Accounts', []))} accounts for org {org_id}")
                return True
            
            print(f"Failed to get accounts. Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error syncing accounts: {str(e)}")
        db.rollback()
        return False