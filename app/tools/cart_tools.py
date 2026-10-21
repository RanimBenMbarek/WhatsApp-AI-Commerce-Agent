
import json
from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from langchain.tools import tool
from pydantic import Field
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.exceptions.cart import CartServiceError
from app.schemas.cart import CartResponse
from app.services.cart_service import CartService


def create_cart_tools(
    customer_id: UUID,
    session_factory: Callable[[], Session] = SessionLocal,
):
    """Create cart tools scoped to one trusted customer identity.

    customer_id must come from trusted application code, never from the LLM.
    """
    @tool
    def add_to_cart(
        variant_id: Annotated[
            UUID,
            Field(description="Exact product variant UUID from catalog results."),
        ],
        quantity: Annotated[
            int,
            Field(ge=1, description="Number of units to add."),
        ] = 1,
    ) -> str:
        """Add a product variant to the current customer's cart.

        If the variant is already in the cart, increase its quantity.
        Do not claim demo prices or demo stock are verified.
        """
        try:
            with session_factory() as session:
                cart_service = CartService(session)
                cart = cart_service.add_item(
                    customer_id=customer_id,
                    variant_id=variant_id,
                    quantity=quantity,
                )
                response = CartResponse.model_validate(cart)
            return json.dumps({
                "success": True,
                "message": "Item added to cart.",
                "cart": response.model_dump(mode="json"),
            })
        except CartServiceError as exc:
            return json.dumps(
                {
                    "success": False,
                    "message": str(exc),
                },
                ensure_ascii=False,
            )

    @tool
    def view_cart() -> str:
        """View the current customer's active cart and its items."""
        try:
            with session_factory() as session:
                cart_service = CartService(session)
                cart = cart_service.get_or_create_active_cart(customer_id=customer_id)
                response = CartResponse.model_validate(cart)
            return json.dumps({
                "success": True,
                "cart": response.model_dump(mode="json"),
            })
        except CartServiceError as exc:
            return json.dumps(
                {
                    "success": False,
                    "message": str(exc),
                },
                ensure_ascii=False,
            )

    return [add_to_cart, view_cart]
