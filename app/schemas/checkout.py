
from dataclasses import dataclass

from app.models.order import Order


@dataclass(frozen=True)
class CheckoutResult:
    order: Order
    invoice_pdf: bytes | None
    invoice_error: str | None = None
