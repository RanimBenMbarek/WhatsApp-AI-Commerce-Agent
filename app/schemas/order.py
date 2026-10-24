
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


OrderStatus = Literal[
    "pending",
    "confirmed",
    "shipped",
    "delivered",
    "cancelled",
]

PaymentStatus = Literal[
    "unpaid",
    "pending",
    "paid",
    "failed",
    "refunded",
]


class PaymentMethod(str, Enum):
    ON_DELIVERY = "on_delivery"
    BY_CARD = "by_card"


class ShippingAddress(BaseModel):
    """Customer-provided delivery address."""

    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(min_length=1, max_length=150)
    phone: str = Field(min_length=1, max_length=30)
    address_line1: str = Field(min_length=1, max_length=250)
    address_line2: str | None = Field(default=None, max_length=250)
    city: str = Field(min_length=1, max_length=100)
    postal_code: str | None = Field(default=None, max_length=30)
    country: str = Field(min_length=1, max_length=100)


class OrderItemRead(BaseModel):
    """An item saved in an order."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    variant_id: UUID
    product_name: str
    sku: str
    variant_description: str | None
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)


class OrderRead(BaseModel):
    """Order information returned by the application."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    order_number: str
    customer_id: UUID
    status: OrderStatus
    payment_status: PaymentStatus
    subtotal: Decimal = Field(ge=0)
    shipping_fee: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)
    shipping_address: dict[str, Any]
    payment_method: PaymentMethod = PaymentMethod.ON_DELIVERY
    carrier: str | None
    tracking_number: str | None
    created_at: datetime
    updated_at: datetime
    shipped_at: datetime | None
    delivered_at: datetime | None
    items: list[OrderItemRead]


class CheckoutRequest(BaseModel):
    """Information needed to prepare checkout."""

    model_config = ConfigDict(extra="forbid")

    shipping_address: ShippingAddress
    payment_method: PaymentMethod = PaymentMethod.ON_DELIVERY


class CheckoutItemPreview(BaseModel):
    """A line in a checkout summary before order creation."""

    variant_id: UUID
    product_name: str
    sku: str
    variant_description: str | None
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)


class CheckoutPreview(BaseModel):
    """Server-calculated totals shown before order confirmation."""

    items: list[CheckoutItemPreview]
    subtotal: Decimal = Field(ge=0)
    shipping_fee: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)
    shipping_address: ShippingAddress
    payment_method: PaymentMethod = PaymentMethod.ON_DELIVERY
    requires_price_verification: bool = False
    requires_stock_verification: bool = False


class ConfirmCheckoutRequest(BaseModel):
    """Explicit confirmation of a previously prepared checkout."""

    confirmation_token: str = Field(min_length=1)
