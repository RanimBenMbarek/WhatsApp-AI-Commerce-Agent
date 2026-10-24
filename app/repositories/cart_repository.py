
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Cart, CartItem
from app.models.product_variant import ProductVariant


class CartRepository:
    """Database access for carts and cart items."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_active_cart_for_customer(
        self,
        customer_id: UUID,
    ) -> Cart | None:
        statement = (
            select(Cart)
            .where(
                Cart.customer_id == customer_id,
                Cart.status == "active",
            )
            .options(
                selectinload(Cart.items).selectinload(CartItem.variant)
            )
            .order_by(Cart.created_at.desc())
            .limit(1)
        )
        return self.db.scalar(statement)

    def get_cart_for_customer(
        self,
        cart_id: UUID,
        customer_id: UUID,
    ) -> Cart | None:
        statement = (
            select(Cart)
            .where(
                Cart.id == cart_id,
                Cart.customer_id == customer_id,
            )
            .options(
                selectinload(Cart.items).selectinload(CartItem.variant)
            )
        )
        return self.db.scalar(statement)

    def create_active_cart(
        self,
        customer_id: UUID,
    ) -> Cart:
        cart = Cart(
            customer_id=customer_id,
            status="active",
        )
        self.db.add(cart)
        self.db.flush()
        return cart

    def get_item_by_variant(
        self,
        cart_id: UUID,
        variant_id: UUID,
    ) -> CartItem | None:
        statement = select(CartItem).where(
            CartItem.cart_id == cart_id,
            CartItem.variant_id == variant_id,
        )
        return self.db.scalar(statement)

    def add_item(
        self,
        cart_id: UUID,
        variant_id: UUID,
        quantity: int,
    ) -> CartItem:
        item = CartItem(
            cart_id=cart_id,
            variant_id=variant_id,
            quantity=quantity,
        )
        self.db.add(item)
        self.db.flush()
        return item

    def update_item_quantity(
        self,
        item: CartItem,
        quantity: int,
    ) -> CartItem:
        item.quantity = quantity
        self.db.flush()
        return item

    def remove_item(self, item: CartItem) -> None:
        self.db.delete(item)
        self.db.flush()

    def get_variant_by_id(self, variant_id: UUID)-> ProductVariant | None:
        statement = select(ProductVariant).where(
            ProductVariant.id == variant_id
        ).options(
            selectinload(ProductVariant.product)
        )
        return self.db.scalar(statement)
