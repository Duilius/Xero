#Servicios que manejarán la lógica de negocio
"""
Este servicio:

1. Maneja la lógica de comparación entre organizaciones
2. Procesa solicitudes de ajuste
3. Maneja aprobaciones
4. Prepara la integración con Xero (pendiente de implementar)
"""
from datetime import datetime, timezone
from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal

from app.models.adjustments import Authorizer, AdjustmentRequest, AdjustmentApproval, AdjustmentStatus
from app.models.user import User
from app.models.organization import Organization
from app.services.xero_client import XeroClient
from app.models.xero_token import XeroToken
from app.services.xero_data_service import get_chart_of_accounts
import json


class AdjustmentService:
    def __init__(self):
        self.xero_client = XeroClient()

    async def get_comparison_data(
   self,
   db: Session,
   org_1_id: str,
   org_2_id: str
) -> Dict:
        try:
            print(f"Getting data for orgs: {org_1_id} and {org_2_id}")
            
            # Obtener tokens
            org_1_token = db.query(XeroToken).filter(
                XeroToken.tenant_id == org_1_id
            ).first()
            
            org_2_token = db.query(XeroToken).filter(
                XeroToken.tenant_id == org_2_id
            ).first()
            
            if not org_1_token or not org_2_token:
                raise ValueError("Missing tokens")
                
            # Obtener datos
            org_1_data = await get_chart_of_accounts(org_1_id, org_1_token.access_token)
            org_2_data = await get_chart_of_accounts(org_2_id, org_2_token.access_token)

            def extract_loan_data(balance_sheet_data) -> Tuple[int, float]:
                reports = balance_sheet_data.get("Reports", [])
                if not reports:
                    return 0, 0
                    
                for row in reports[0].get("Rows", []):
                    if (row.get("RowType") == "Section" and 
                        row.get("Title", "").upper() == "NON-CURRENT LIABILITIES"):
                        
                        loan_amount = 0
                        loan_count = 0
                        
                        for subrow in row.get("Rows", []):
                            if subrow.get("RowType") == "Row":
                                cells = subrow.get("Cells", [])
                                if len(cells) >= 2 and "Loan" in cells[0].get("Value", ""):
                                    try:
                                        amount = float(cells[1].get("Value", "0"))  # No removemos el signo
                                        loan_amount = amount  # Solo tomamos el valor del préstamo
                                        loan_count = 1 if amount != 0 else 0
                                        print(f"Found loan: {cells[0].get('Value')}, amount: {amount}")
                                    except (ValueError, TypeError):
                                        continue
                        
                        return loan_count, loan_amount
                
                return 0, 0

            # Extraer datos de préstamos
            org_1_count, org_1_amount = extract_loan_data(org_1_data)
            org_2_count, org_2_amount = extract_loan_data(org_2_data)
            
            return {
                "org_1": {
                    "name": org_1_data["Reports"][0]["ReportTitles"][1],
                    "transaction_count": org_1_count,
                    "amount": org_1_amount
                },
                "org_2": {
                    "name": org_2_data["Reports"][0]["ReportTitles"][1],
                    "transaction_count": org_2_count,
                    "amount": org_2_amount
                },
                "discrepancy": abs(org_1_amount - org_2_amount)
            }
            
        except Exception as e:
            print(f"Error getting comparison data: {str(e)}")
            raise

    async def create_adjustment_request(
        self,
        db: Session,
        user: User,
        adjust_in_org_id: int,
        amount: Decimal,
        justification: str,
        authorizer_ids: List[int]
    ) -> AdjustmentRequest:
        """Crear una solicitud de ajuste."""
        try:
            # Verificar que los autorizadores existen y están activos
            authorizers = db.query(Authorizer).filter(
                Authorizer.id.in_(authorizer_ids),
                Authorizer.is_active == True
            ).all()

            if len(authorizers) != len(authorizer_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more authorizers are invalid or inactive"
                )

            # Crear la solicitud
            request = AdjustmentRequest(
                organization_id=user.organization_id,
                requestor_id=user.id,
                adjust_in_org_id=adjust_in_org_id,
                amount=amount,
                justification=justification,
                status=AdjustmentStatus.PENDING
            )
            db.add(request)
            db.flush()

            # Crear las aprobaciones pendientes
            for authorizer_id in authorizer_ids:
                approval = AdjustmentApproval(
                    request_id=request.id,
                    authorizer_id=authorizer_id
                )
                db.add(approval)

            db.commit()
            return request

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error creating adjustment request: {str(e)}"
            )

    async def process_approval(
        self,
        db: Session,
        request_id: int,
        authorizer_id: int,
        status: AdjustmentStatus,
        comment: Optional[str] = None
    ) -> AdjustmentApproval:
        """Procesar una aprobación de ajuste."""
        try:
            # Obtener y actualizar la aprobación
            approval = db.query(AdjustmentApproval).filter(
                AdjustmentApproval.request_id == request_id,
                AdjustmentApproval.authorizer_id == authorizer_id
            ).first()

            if not approval:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Approval not found"
                )

            approval.status = status
            approval.comment = comment
            db.flush()

            # Verificar si todas las aprobaciones están completas
            request = db.query(AdjustmentRequest).get(request_id)
            all_approvals = db.query(AdjustmentApproval).filter(
                AdjustmentApproval.request_id == request_id
            ).all()

            if all(a.status == AdjustmentStatus.APPROVED for a in all_approvals):
                # Todos aprobaron - proceder con el ajuste en Xero
                await self._apply_adjustment_to_xero(db, request)
                request.status = AdjustmentStatus.APPROVED
            elif any(a.status == AdjustmentStatus.REJECTED for a in all_approvals):
                # Al menos uno rechazó
                request.status = AdjustmentStatus.REJECTED

            db.commit()
            return approval

        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error processing approval: {str(e)}"
            )

    async def _get_org_data(self, db: Session, org_id: int) -> Dict:
        """Obtener datos de una organización desde Xero."""
        # TODO: Implementar la lógica real de Xero
        return {
            "transaction_count": 0,
            "total_amount": Decimal('0.00')
        }

    async def _apply_adjustment_to_xero(
        self,
        db: Session,
        request: AdjustmentRequest
    ) -> None:
        """Aplicar el ajuste en Xero una vez aprobado."""
        # TODO: Implementar la lógica real de ajuste en Xero
        pass

adjustment_service = AdjustmentService()