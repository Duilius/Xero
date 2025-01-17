from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.xero_token import XeroToken
from app.services.xero_data_service import get_chart_of_accounts
from typing import List, Dict

router = APIRouter()

@router.get("/")
async def read_organizations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return {"message": "List organizations endpoint"}



@router.get("/{org_id}/related-loans")
async def get_related_loans(org_id: str, db: Session = Depends(get_db)):
    try:
        token = db.query(XeroToken).filter(XeroToken.tenant_id == org_id).first()
        accounts = await get_chart_of_accounts(tenant_id=org_id, access_token=token.access_token)
        
        related_orgs = []
        if accounts and "Reports" in accounts:
            for row in accounts["Reports"][0].get("Rows", []):
                if row.get("RowType") == "Section" and "Non-current Liabilities" in row.get("Title", ""):
                    for subrow in row.get("Rows", []):
                        if "Loan" in subrow.get("Cells", [])[0].get("Value", ""):
                            amount = float(subrow["Cells"][1]["Value"].replace(",", ""))
                            if amount != 0:  # Solo incluir si hay un préstamo activo
                                org_name = subrow["Cells"][0]["Value"].replace("Loan-1 to ", "").replace("Loan to ", "")
                                related_orgs.append({
                                    "id": org_id,
                                    "name": org_name,
                                    "amount": abs(amount),
                                    "is_debtor": amount > 0
                                })
        
        return [org for org in related_orgs if org["amount"] > 0]  # Solo retornar préstamos activos
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))