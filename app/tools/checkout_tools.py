
import json
from decimal import Decimal
from typing import Literal
from uuid import UUID

from langchain.tools import tool
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.repositories.cart_repository import CartRepository
from app.repositories.order_repository import OrderRepository
from app.services.order_service import OrderService


def create_checkout_tools(
    customer_id: UUID,
    shipping_fee: Decimal | None = None,
    session_factory=SessionLocal,
):
    """Create checkout tools scoped to one trusted customer."""

    @tool
    def preview_checkout(
        full_name: str,
        phone: str,
        address_line1: str,
        city: str,
        country: str,
        address_line2: str | None = None,
        postal_code: str | None = None,
        payment_method: Literal["on_delivery", "by_card"] = "on_delivery",
    ) -> str:
        """Preview the current customer's checkout.

        Shows cart items, quantities, prices, shipping details, and totals.
        This tool does not create an order or modify the cart.
        The customer must review the preview before any order is created.
        """

        if shipping_fee is None:
            return json.dumps({
                "success": False,
                "error": "Checkout is unavailable because the shipping fee "
                         "has not been configured.",
            })

        shipping_address = {
            "full_name": full_name,
            "phone": phone,
            "address_line1": address_line1,
            "address_line2": address_line2,
            "city": city,
            "postal_code": postal_code,
            "country": country,
        }

        try:
            settings = get_settings()

            with session_factory() as db:
                cart_repository = CartRepository(db)
                order_repository = OrderRepository(db)

                order_service = OrderService(
                    db=db,
                    cart_repository=cart_repository,
                    order_repository=order_repository,
                    seller_name=settings.seller_name,
                    seller_address=settings.seller_address,
                )

                preview = order_service.preview_checkout(
                    customer_id=customer_id,
                    shipping_address=shipping_address,
                    shipping_fee=shipping_fee,
                    payment_method=payment_method,
                )

                return json.dumps(
                    {
                        "success": True,
                        "preview": preview.model_dump(mode="json"),
                    },
                    ensure_ascii=False,
                )

        except (ValidationError, ValueError) as exc:
            return json.dumps({
                "success": False,
                "error": str(exc),
            }, ensure_ascii=False)

        except Exception:
            return json.dumps({
                "success": False,
                "error": "Unable to prepare checkout. Please try again.",
            })

    return [preview_checkout]
