from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.xero_token import XeroToken
from app.services.xero_data_service import get_chart_of_accounts
from typing import Dict
import httpx

router = APIRouter()

@router.get("/details/{lender_id}/{borrower_id}")
async def get_loan_details(lender_id: str, borrower_id: str, db: Session = Depends(get_db)):
    try:
        lender_token = db.query(XeroToken).filter(XeroToken.tenant_id == lender_id).first()
        
        # Obtener monto original del préstamo
        balance_sheet = await get_chart_of_accounts(
            tenant_id=lender_id,
            access_token=lender_token.access_token
        )

        loan_amount = 0
        if balance_sheet and "Reports" in balance_sheet:
            for row in balance_sheet["Reports"][0].get("Rows", []):
                if row.get("RowType") == "Section" and "Non-Current Liabilities" in row.get("Title", ""):
                    for subrow in row.get("Rows", []):
                        if "Loan" in subrow.get("Cells", [])[0].get("Value", ""):
                            amount = float(subrow["Cells"][1]["Value"].replace(",", ""))
                            if amount < 0:
                                loan_amount = abs(amount)

        # Obtener historial de pagos
        payments = await get_payment_history(
            lender_token.access_token,
            lender_id,
            borrower_id
        )
        
        total_payments = sum(payment["amount"] for payment in payments)
        current_balance = loan_amount - total_payments

        return {
            "originalAmount": loan_amount,
            "totalPayments": total_payments,
            "currentBalance": current_balance,
            "payments": payments,
            "discrepancy": False
        }

    except Exception as e:
        print(f"ERROR: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

async def get_loan_amount(access_token: str, lender_id: str, borrower_id: str) -> Dict:
    """Obtener monto del préstamo del Balance Sheet"""
    balance_sheet = await get_chart_of_accounts(lender_id, access_token)
    loan_amount = 0
    
    if balance_sheet and "Reports" in balance_sheet:
        for row in balance_sheet["Reports"][0].get("Rows", []):
            if row.get("RowType") == "Section" and "Non-current Liabilities" in row.get("Title", ""):
                for subrow in row.get("Rows", []):
                    if "Loan" in subrow.get("Cells", [])[0].get("Value", ""):
                        amount = float(subrow["Cells"][1]["Value"].replace(",", ""))
                        if amount < 0:  # Préstamo otorgado
                            loan_amount = abs(amount)

    return {"amount": loan_amount}

async def get_payment_history(access_token: str, lender_id: str, borrower_id: str) -> list:
    """Buscar pagos del préstamo en Xero"""
    print(f"DEBUG - Buscando pagos entre {lender_id} y {borrower_id}")
    
    url = "https://api.xero.com/api.xro/2.0/BankTransactions"
    payments = []
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Xero-tenant-id": lender_id,
                    "Accept": "application/json"
                },
                params={
                    "where": "Type==\"RECEIVE\" AND Status==\"AUTHORISED\""  # Pagos recibidos y autorizados
                }
            )
            
            if response.status_code == 200:
                transactions = response.json().get("BankTransactions", [])
                print(f"DEBUG - Encontradas {len(transactions)} transacciones")
                
                for tx in transactions:
                    # Buscar transacciones que mencionen "loan" o "préstamo"
                    reference = tx.get("Reference", "").lower()
                    description = tx.get("LineItems", [{}])[0].get("Description", "").lower()
                    
                    if "loan" in reference or "loan" in description:
                        payments.append({
                            "date": tx["Date"],
                            "amount": float(tx["Total"]),
                            "type": "Payment",
                            "status": tx["Status"],
                            "reference": tx.get("Reference", "")
                        })
                        print(f"DEBUG - Encontrado pago: {tx['Date']} - ${tx['Total']}")
            
            else:
                print(f"DEBUG - Error al obtener transacciones: {response.status_code}")
    
    except Exception as e:
        print(f"ERROR buscando pagos: {str(e)}")
    
    return sorted(payments, key=lambda x: x["date"])


@router.get("/test")
async def test_endpoint():
    return {"message": "Loans endpoint working"}