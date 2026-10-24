
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class InvoiceLineItem(BaseModel):
    """A line item copied from the saved order."""

    model_config = ConfigDict(extra="forbid")

    product_name: str
    sku: str
    variant_description: str | None = None
    quantity: int = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    line_total: Decimal = Field(ge=0)


class InvoiceData(BaseModel):
    """Data needed to render a commercial invoice PDF."""

    model_config = ConfigDict(extra="forbid")

    invoice_number: str
    issued_at: datetime

    order_number: str
    order_status: str
    payment_status: str

    seller_name: str
    seller_address: str
    seller_contact: str | None = None

    customer_name: str
    shipping_address: dict[str, Any]

    items: list[InvoiceLineItem] = Field(min_length=1)

    subtotal: Decimal = Field(ge=0)
    shipping_fee: Decimal = Field(ge=0)
    total: Decimal = Field(ge=0)

    currency: str = Field(min_length=1, max_length=10)
