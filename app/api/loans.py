from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.xero_token import XeroToken
from app.services.xero_data_service import get_chart_of_accounts
from typing import Dict
import httpx
import traceback  # Agregar este import
from datetime import datetime, timezone

router = APIRouter()

@router.get("/details/{lender_id}/{borrower_id}")
async def get_loan_details(lender_id: str, borrower_id: str, db: Session = Depends(get_db)):
    try:
        # Obtener tokens
        lender_token = db.query(XeroToken).filter(XeroToken.tenant_id == lender_id).first()
        borrower_token = db.query(XeroToken).filter(XeroToken.tenant_id == borrower_id).first()
        print("DEBUG - Tokens obtenidos")
        
        # Obtener monto original del préstamo
        balance_sheet = await get_chart_of_accounts(
            tenant_id=lender_id,
            access_token=lender_token.access_token
        )
        print("DEBUG - Balance sheet obtenido")

        loan_amount = 0
        if balance_sheet and "Reports" in balance_sheet:
            for row in balance_sheet["Reports"][0].get("Rows", []):
                if row.get("RowType") == "Section" and "Non-Current Liabilities" in row.get("Title", ""):
                    print("DEBUG - Sección Non-Current Liabilities encontrada")
                    for subrow in row.get("Rows", []):
                        cell_value = subrow.get("Cells", [])[0].get("Value", "")
                        print(f"DEBUG - Revisando fila: {cell_value}")
                        if "Loan" in cell_value:
                            amount = float(subrow["Cells"][1]["Value"].replace(",", ""))
                            print(f"DEBUG - Monto encontrado: {amount}")
                            if amount < 0:  # Préstamo otorgado
                                loan_amount = abs(amount)
                                print(f"DEBUG - Monto del préstamo: {loan_amount}")

        # Obtener comparación de pagos
        payments_data = await get_payment_history(
            lender_token.access_token,
            borrower_token.access_token,
            lender_id,
            borrower_id
        )

        total_payments = sum(payment["borrower_amount"] or 0 for payment in payments_data["comparison"])
        current_balance = loan_amount - total_payments

        print(f"DEBUG - Final: loan={loan_amount}, payments={total_payments}, balance={current_balance}")

        return {
            "originalAmount": loan_amount,
            "totalPayments": total_payments,
            "currentBalance": current_balance,
            "payments": payments_data
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

def parse_xero_date(xero_date: str) -> str:
    """Convierte fecha de Xero a formato ISO"""
    try:
        # Extraer el timestamp
        timestamp = int(xero_date.replace('/Date(', '').replace('+0000)/', ''))
        # Usar datetime.utcfromtimestamp en lugar de fromtimestamp
        # Usar datetime.fromtimestamp con timezone explícito
        date_obj = datetime.fromtimestamp(timestamp/1000, tz=timezone.utc)
        return date_obj.isoformat()
    except Exception as e:
        print(f"Error parsing date: {e}")
        return xero_date


async def get_payment_history(lender_token: str, borrower_token: str, lender_id: str, borrower_id: str) -> dict:
    print("DEBUG - Inicio get_payment_history")
    
    # Obtener pagos
    lender_payments = await get_transactions(lender_token, lender_id, True) or []
    borrower_payments = await get_transactions(borrower_token, borrower_id, False) or []
    
    print(f"DEBUG - Estructura de pagos a comparar:")
    print(f"Prestamista: {lender_payments}")
    print(f"Prestatario: {borrower_payments}")

    # Crear comparación
    comparison = []
    if borrower_payments:  # Si hay pagos del prestatario
        for payment in borrower_payments:
            comparison.append({
                "date": payment["date"],
                "borrower_amount": payment["amount"],
                "lender_amount": None,  # Ningún pago registrado por el prestamista
                "status": "UNRECONCILED"
            })
    
    result = {
        "comparison": comparison,
        "needs_reconciliation": len(comparison) > 0
    }
    
    print(f"DEBUG - Resultado final de comparación: {result}")
    return result
    
async def get_transactions(token: str, tenant_id: str, is_lender: bool) -> list:
   url = "https://api.xero.com/api.xro/2.0/BankTransactions"
   try:
       async with httpx.AsyncClient() as client:
           print(f"DEBUG - Requesting transactions for {'lender' if is_lender else 'borrower'}")
           response = await client.get(
               url,
               headers={
                   "Authorization": f"Bearer {token}",
                   "Xero-tenant-id": tenant_id,
                   "Accept": "application/json"
               }
           )
           print(f"DEBUG - Response status: {response.status_code}")
           if response.status_code == 200:
               transactions = response.json().get("BankTransactions", [])
               print(f"DEBUG - Found {len(transactions)} transactions")
               payments = []
               for tx in transactions:
                   if (is_lender and tx.get("Type") == "RECEIVE") or (not is_lender and tx.get("Type") == "SPEND"):
                       if "loan" in tx.get("Reference", "").lower():
                           payments.append({
                               "date": parse_xero_date(tx["Date"]),
                               "amount": abs(float(tx["Total"])),
                               "reference": tx.get("Reference", ""),
                               "status": tx["Status"]
                           })
                           print(f"DEBUG - Found payment: {payments[-1]}")
               return payments
           else:
               print(f"DEBUG - Error response: {response.text}")
               return []
   except Exception as e:
       print(f"Error getting transactions: {str(e)}")
       print(f"DEBUG - Full error: {e.__class__.__name__}")
       return []

@router.get("/test")
async def test_endpoint():
    return {"message": "Loans endpoint working"}    