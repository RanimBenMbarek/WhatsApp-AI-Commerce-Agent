
import json
from collections.abc import Callable
from typing import Annotated
from uuid import UUID

from langchain.tools import ToolRuntime, tool
from pydantic import Field
from sqlalchemy.orm import Session

from app.agents.context import CommerceAgentContext
from app.db.session import SessionLocal
from app.exceptions.cart import CartServiceError
from app.schemas.cart import CartResponse
from app.services.cart_service import CartService


def create_cart_tools(
    session_factory: Callable[[], Session] = SessionLocal,
):
    """Create cart tools that use trusted runtime customer context."""

    def get_customer_id(
        runtime: ToolRuntime[CommerceAgentContext],
    ) -> UUID:
        """Get the authenticated customer ID from application context."""
        customer_id = runtime.context.get("customer_id")

        if customer_id is None:
            raise ValueError(
                "Cart operations require an authenticated customer."
            )

        return customer_id

    @tool
    def add_to_cart(
        variant_id: Annotated[
            UUID,
            Field(description="Exact product variant UUID from catalog results."),
        ],
        runtime: ToolRuntime[CommerceAgentContext],
        quantity: Annotated[
            int,
            Field(ge=1, description="Number of units to add."),
        ] = 1,
    ) -> str:
        """Add a product variant to the customer's cart.

        If the variant already exists, increase its quantity.
        """
        try:
            customer_id = get_customer_id(runtime)

            with session_factory() as session:
                cart = CartService(session).add_item(
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
            return json.dumps({
                "success": False,
                "message": str(exc),
            }, ensure_ascii=False)

    @tool
    def view_cart(
        runtime: ToolRuntime[CommerceAgentContext],
    ) -> str:
        """View the customer's active cart and its items."""
        try:
            customer_id = get_customer_id(runtime)

            with session_factory() as session:
                cart = CartService(session).get_or_create_active_cart(
                    customer_id=customer_id,
                )
                response = CartResponse.model_validate(cart)

            return json.dumps({
                "success": True,
                "cart": response.model_dump(mode="json"),
            })
        except CartServiceError as exc:
            return json.dumps({
                "success": False,
                "message": str(exc),
            }, ensure_ascii=False)

    @tool
    def update_cart_item(
        item_id: Annotated[
            UUID,
            Field(description="UUID of an item in the customer's cart."),
        ],
        quantity: Annotated[
            int,
            Field(ge=1, description="New total quantity for this item."),
        ],
        runtime: ToolRuntime[CommerceAgentContext],
    ) -> str:
        """Change the quantity of an item in the active cart.

        Quantity means the new total, not the additional amount.
        """
        try:
            customer_id = get_customer_id(runtime)

            with session_factory() as session:
                cart = CartService(session).update_item_quantity(
                    customer_id=customer_id,
                    item_id=item_id,
                    quantity=quantity,
                )
                response = CartResponse.model_validate(cart)

            return json.dumps({
                "success": True,
                "message": "Cart item quantity updated.",
                "cart": response.model_dump(mode="json"),
            })
        except CartServiceError as exc:
            return json.dumps({
                "success": False,
                "message": str(exc),
            }, ensure_ascii=False)

    @tool
    def remove_from_cart(
        item_id: Annotated[
            UUID,
            Field(description="UUID of an item in the customer's cart."),
        ],
        runtime: ToolRuntime[CommerceAgentContext],
    ) -> str:
        """Remove an item from the customer's active cart."""
        try:
            customer_id = get_customer_id(runtime)

            with session_factory() as session:
                cart = CartService(session).remove_item(
                    customer_id=customer_id,
                    item_id=item_id,
                )
                response = CartResponse.model_validate(cart)

            return json.dumps({
                "success": True,
                "message": "Item removed from cart.",
                "cart": response.model_dump(mode="json"),
            }, ensure_ascii=False)
        except CartServiceError as exc:
            return json.dumps({
                "success": False,
                "message": str(exc),
            }, ensure_ascii=False)

    return [
        add_to_cart,
        view_cart,
        update_cart_item,
        remove_from_cart,
    ]
