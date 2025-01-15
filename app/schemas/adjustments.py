#Schemas Pydantic para la validación de datos en la API.
"""
Estos schemas:

Validan datos de entrada/salida
Definen la estructura de las requests/responses
Incluyen validaciones específicas (ej: longitud mínima de justificación)

Uso de Field para validaciones
Decimal para valores monetarios
Validación de longitud mínima usando Field
¿Procedemos con los endpoints de la API?
"""

from pydantic import BaseModel, EmailStr, Field
from decimal import Decimal
from typing import Optional, List
from datetime import datetime
from enum import Enum

class AdjustmentStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"

class AuthorizerBase(BaseModel):
    email: EmailStr
    name: str
    role: str
    is_active: bool = True

class AuthorizerCreate(AuthorizerBase):
    organization_id: int

class AuthorizerResponse(AuthorizerBase):
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class AdjustmentRequestBase(BaseModel):
    adjust_in_org_id: int
    amount: Decimal = Field(..., decimal_places=2, ge=0)  # Cambiado aquí
    justification: str = Field(..., min_length=10)        # Cambiado aquí
    comparison_data: Optional[dict] = None

class AdjustmentRequestCreate(AdjustmentRequestBase):
    authorizer_ids: List[int]

class AdjustmentRequestResponse(AdjustmentRequestBase):
    id: int
    organization_id: int
    requestor_id: int
    status: AdjustmentStatus
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ApprovalCreate(BaseModel):
    status: AdjustmentStatus
    comment: Optional[str] = None

class ApprovalResponse(ApprovalCreate):
    id: int
    request_id: int
    authorizer_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True