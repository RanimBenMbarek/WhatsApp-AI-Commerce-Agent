
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class CartItemAddRequest(BaseModel):
    variant_id: UUID
    quantity: int = Field(gt=0)


class CartItemUpdateRequest(BaseModel):
    quantity: int = Field(gt=0)


class CartVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sku: str
    size: str | None
    color: str | None
    price: Decimal
    price_is_demo: bool


class CartItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    variant_id: UUID
    quantity: int
    created_at: datetime
    updated_at: datetime
    variant: CartVariantResponse


class CartResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    created_at: datetime
    updated_at: datetime
    items: list[CartItemResponse] = Field(default_factory=list)
