"""
Este código:

1. Maneja autorizadores por organización
2. Permite crear y listar solicitudes de ajuste
3. Gestiona aprobaciones de ajustes
4. Incluye verificaciones de seguridad
"""


from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone
from app.db.session import get_db
from app.schemas.adjustments import (
    AuthorizerCreate, AuthorizerResponse,
    AdjustmentRequestCreate, AdjustmentRequestResponse,
    ApprovalCreate, ApprovalResponse
)
from app.models.adjustments import Authorizer, AdjustmentRequest, AdjustmentApproval
from app.models.user import User
from app.core.middlewares import get_current_user_id

router = APIRouter(prefix="/adjustments", tags=["adjustments"])

# Endpoints para Autorizadores
@router.post("/authorizers/", response_model=AuthorizerResponse)
async def create_authorizer(
    authorizer: AuthorizerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id)
):
    db_authorizer = Authorizer(**authorizer.model_dump())
    db.add(db_authorizer)
    db.commit()
    db.refresh(db_authorizer)
    return db_authorizer

@router.get("/authorizers/{org_id}", response_model=List[AuthorizerResponse])
async def get_authorizers(
    org_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id)
):
    return db.query(Authorizer).filter(
        Authorizer.organization_id == org_id,
        Authorizer.is_active == True
    ).all()

# Endpoints para Solicitudes de Ajuste
@router.post("/requests/", response_model=AdjustmentRequestResponse)
async def create_adjustment_request(
    request: AdjustmentRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id)
):
    # Crear la solicitud
    adjustment_request = AdjustmentRequest(
        **request.model_dump(exclude={'authorizer_ids'}),
        organization_id=current_user.organization_id,
        requestor_id=current_user.id
    )
    db.add(adjustment_request)
    db.commit()
    db.refresh(adjustment_request)

    # Crear las aprobaciones pendientes
    for authorizer_id in request.authorizer_ids:
        approval = AdjustmentApproval(
            request_id=adjustment_request.id,
            authorizer_id=authorizer_id
        )
        db.add(approval)
    
    db.commit()
    return adjustment_request

@router.get("/requests/", response_model=List[AdjustmentRequestResponse])
async def get_adjustment_requests(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id)
):
    return db.query(AdjustmentRequest).filter(
        AdjustmentRequest.organization_id == current_user.organization_id
    ).all()

# Endpoint para Aprobaciones
@router.post("/requests/{request_id}/approve", response_model=ApprovalResponse)
async def create_approval(
    request_id: int,
    approval: ApprovalCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_id)
):
    # Verificar que el usuario es un autorizador válido
    authorizer = db.query(Authorizer).filter(
        Authorizer.organization_id == current_user.organization_id,
        Authorizer.is_active == True
    ).first()
    
    if not authorizer:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User is not an authorized approver"
        )

    # Buscar la aprobación pendiente
    approval_record = db.query(AdjustmentApproval).filter(
        AdjustmentApproval.request_id == request_id,
        AdjustmentApproval.authorizer_id == authorizer.id
    ).first()

    if not approval_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Approval request not found"
        )

    # Actualizar la aprobación
    for key, value in approval.model_dump().items():
        setattr(approval_record, key, value)

    db.commit()
    db.refresh(approval_record)
    return approval_record