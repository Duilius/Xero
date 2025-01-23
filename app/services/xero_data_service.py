from fastapi import Depends
from app.db.session import get_db
import json
import httpx
from typing import Optional, Dict, List
from app.services.xero_auth_service import XeroAuthService
from sqlalchemy.orm import Session

async def get_chart_of_accounts(
    tenant_id: str, 
    access_token: str,
    xero_auth_service: XeroAuthService,  # Inyectar el servicio
    db: Session = Depends(get_db)
) -> Dict:
    """Obtener balance sheet detallado de Xero"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.xero.com/api.xro/2.0/Reports/BalanceSheet",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Xero-tenant-id": tenant_id,
                    "Accept": "application/json"
                }
            )
            
            if response.status_code == 401:  # Token expirado
                print("DEBUG - Token expired, attempting refresh")
                new_token = await xero_auth_service.refresh_access_token(tenant_id, db)
                return await get_chart_of_accounts(
                    tenant_id, 
                    new_token, 
                    xero_auth_service,  # Pasar el servicio en la recursión
                    db
                )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"ERROR - Failed to get balance sheet: {response.text}")
                return None
                
    except Exception as e:
        print(f"ERROR in get_chart_of_accounts: {str(e)}")
        return None

async def get_loan_accounts(token: str, tenant_id: str) -> List[Dict]:
    """Obtener préstamos usando Account IDs"""
    loans = []
    balance_sheet = await get_chart_of_accounts(tenant_id, token)
    
    print(f"DEBUG - Buscando préstamos para tenant: {tenant_id}")
    
    if balance_sheet and "Reports" in balance_sheet:
        report = balance_sheet["Reports"][0]
        organization_name = report.get("ReportTitles", [])[1] if len(report.get("ReportTitles", [])) > 1 else "Unknown"
        
        for row in report.get("Rows", []):
            if row.get("RowType") == "Section" and "Liabilities" in row.get("Title", ""):
                for subrow in row.get("Rows", []):
                    if subrow.get("RowType") == "Row":
                        cells = subrow.get("Cells", [])
                        if cells and "Loan" in cells[0].get("Value", "").lower():
                            account_attrs = cells[0].get("Attributes", [])
                            if account_attrs:
                                account_id = account_attrs[0].get("Value")
                                amount = float(cells[1].get("Value", "0").replace(",", ""))
                                loan_name = cells[0].get("Value", "")
                                
                                loans.append({
                                    "account_id": account_id,
                                    "organization_name": organization_name,
                                    "loan_name": loan_name,
                                    "amount": amount,  # Mantener el signo para saber quién debe a quién
                                    "tenant_id": tenant_id,
                                    "date": report.get("ReportDate"),
                                    "is_borrower": amount > 0,  # True si debe dinero
                                    "is_lender": amount < 0     # True si prestó dinero
                                })
                                print(f"DEBUG - Found loan: {loan_name}, amount: {amount}, account_id: {account_id}")
    
    return loans

async def get_related_payments(account_id: str, start_date: str = None, end_date: str = None):
   """Buscar pagos relacionados a un Account ID específico"""
   # Implementaremos el filtro por fechas aquí