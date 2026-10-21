from uuid import UUID

from sqlalchemy.orm import Session

from app.models.cart import Cart
from app.models.cart_item import CartItem
from app.models.product_variant import ProductVariant
from app.repositories.cart_repository import CartRepository
from app.exceptions.cart import (
    CartNotFoundError,
    InsufficientStockError,
    InvalidQuantityError,
    VariantUnavailableError,
)


class CartService:
    """Business logic for customer carts."""

    def __init__(self, db: Session) -> None:
        self.db = db
        self.cart_repository = CartRepository(db)

    @staticmethod
    def _validate_quantity(quantity: int) -> None:
        if quantity < 1:
            raise InvalidQuantityError("Quantity must be at least 1.")

    @staticmethod
    def _validate_variant(variant: ProductVariant | None) -> ProductVariant:
        if (
            variant is None
            or not variant.is_active
            or variant.product is None
            or variant.product.status != "active"
        ):
            raise VariantUnavailableError(
                "This product variant is unavailable."
            )

        return variant

    @staticmethod
    def _validate_stock(
        variant: ProductVariant,
        requested_quantity: int,
    ) -> None:
        # Demo stock is not verified inventory.
        if (
            not variant.stock_is_demo
            and requested_quantity > variant.stock_quantity
        ):
            raise InsufficientStockError(
                "The requested quantity exceeds available stock."
            )

    def _reload_active_cart(self, customer_id: UUID) -> Cart:
        cart = self.cart_repository.get_active_cart_for_customer(
            customer_id
        )
        if cart is None:
            raise CartNotFoundError("No active cart was found.")
        return cart

    def get_or_create_active_cart(self, customer_id: UUID) -> Cart:
        try:
            cart = self.cart_repository.get_active_cart_for_customer(
                customer_id
            )

            if cart is not None:
                return cart

            self.cart_repository.create_active_cart(customer_id)
            self.db.commit()

            return self._reload_active_cart(customer_id)

        except Exception:
            self.db.rollback()
            raise

    def add_item(
        self,
        customer_id: UUID,
        variant_id: UUID,
        quantity: int,
    ) -> Cart:
        self._validate_quantity(quantity)

        try:
            variant = self._validate_variant(
                self.cart_repository.get_variant_by_id(variant_id)
            )

            cart = self.cart_repository.get_active_cart_for_customer(
                customer_id
            )

            if cart is None:
                cart = self.cart_repository.create_active_cart(
                    customer_id
                )

            existing_item = self.cart_repository.get_item_by_variant(
                cart.id,
                variant_id,
            )

            new_quantity = quantity
            if existing_item is not None:
                new_quantity += existing_item.quantity

            self._validate_stock(variant, new_quantity)

            if existing_item is not None:
                self.cart_repository.update_item_quantity(
                    existing_item,
                    new_quantity,
                )
            else:
                self.cart_repository.add_item(
                    cart.id,
                    variant_id,
                    quantity,
                )

            self.db.commit()
            return self._reload_active_cart(customer_id)

        except Exception:
            self.db.rollback()
            raise

    def update_item_quantity(
        self,
        customer_id: UUID,
        item_id: UUID,
        quantity: int,
    ) -> Cart:
        self._validate_quantity(quantity)

        try:
            cart = self.cart_repository.get_active_cart_for_customer(
                customer_id
            )

            if cart is None:
                raise CartNotFoundError("No active cart was found.")

            item = next(
                (item for item in cart.items if item.id == item_id),
                None,
            )

            if item is None:
                raise CartNotFoundError(
                    "The requested item was not found in this cart."
                )

            variant = self._validate_variant(item.variant)
            self._validate_stock(variant, quantity)

            self.cart_repository.update_item_quantity(item, quantity)
            self.db.commit()

            return self._reload_active_cart(customer_id)

        except Exception:
            self.db.rollback()
            raise

    def remove_item(
        self,
        customer_id: UUID,
        item_id: UUID,
    ) -> Cart:
        try:
            cart = self.cart_repository.get_active_cart_for_customer(
                customer_id
            )

            if cart is None:
                raise CartNotFoundError("No active cart was found.")

            item = next(
                (item for item in cart.items if item.id == item_id),
                None,
            )

            if item is None:
                raise CartNotFoundError(
                    "The requested item was not found in this cart."
                )

            self.cart_repository.remove_item(item)
            self.db.commit()

            return self._reload_active_cart(customer_id)

        except Exception:
            self.db.rollback()
            raise
