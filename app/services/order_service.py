from decimal import Decimal, ROUND_HALF_UP
from enum import Enum
from typing import Any
from uuid import UUID, uuid4
import logging

from sqlalchemy.orm import Session

from app.exceptions.cart import (
    CartNotFoundError,
    VariantUnavailableError,
)
from app.exceptions.order import (
    CheckoutNotConfirmedError,
    DemoCatalogDataError,
    EmptyCartError,
    InvalidShippingFeeError,
    OrderNotFoundError,
)
from app.models.cart import Cart
from app.models.order import (
    Order,
    OrderStatus,
    PaymentMethod,
    PaymentStatus,
)
from app.models.order_item import OrderItem
from app.repositories.cart_repository import CartRepository
from app.repositories.order_repository import OrderRepository
from app.schemas.checkout import CheckoutResult
from app.services.invoice_service import InvoiceService
from app.schemas.order import (
    CheckoutItemPreview,
    CheckoutPreview,
    PaymentMethod as CheckoutPaymentMethod,
    ShippingAddress as ShippingAddressSchema,
)

logger = logging.getLogger(__name__)

CENT = Decimal("0.01")


class OrderService:
    """Business logic for checkout and customer orders."""

    def __init__(
        self,
        db: Session,
        *,
        seller_name: str | None = None,
        seller_address: str | None = None,
        seller_contact: str | None = None,
        currency: str = "EUR",
    ) -> None:
        self.db = db
        self.cart_repository = CartRepository(db)
        self.order_repository = OrderRepository(db)

        # Keep support for configuring the invoice service here.
        self.invoice_service: InvoiceService | None = None

        if seller_name and seller_address:
            self.invoice_service = InvoiceService(
                db,
                seller_name=seller_name,
                seller_address=seller_address,
                seller_contact=seller_contact,
                currency=currency,
            )

    @staticmethod
    def _money(value: Decimal) -> Decimal:
        return value.quantize(CENT, rounding=ROUND_HALF_UP)

    @staticmethod
    def _validate_shipping_fee(shipping_fee: Decimal) -> None:
        if not shipping_fee.is_finite() or shipping_fee < 0:
            raise InvalidShippingFeeError(
                "Shipping fee must be a finite, non-negative amount."
            )

    @staticmethod
    def _validate_cart(cart: Cart) -> None:
        if not cart.items:
            raise EmptyCartError("Cannot create an order from an empty cart.")

        for item in cart.items:
            variant = item.variant

            if (
                variant is None
                or not variant.is_active
                or variant.product is None
                or variant.product.status != "active"
            ):
                raise VariantUnavailableError(
                    "A product in the cart is no longer available."
                )

            if variant.price_is_demo:
                raise DemoCatalogDataError(
                    "Order creation requires verified product prices."
                )

            if variant.stock_is_demo:
                raise DemoCatalogDataError(
                    "Order creation requires verified inventory."
                )

            if item.quantity < 1:
                raise EmptyCartError(
                    "Every order item must have a positive quantity."
                )

            if item.quantity > variant.stock_quantity:
                raise DemoCatalogDataError(
                    "A requested quantity exceeds verified stock."
                )

    @staticmethod
    def _variant_description(variant: Any) -> str | None:
        parts: list[str] = []

        if variant.size:
            parts.append(f"Size: {variant.size}")

        if variant.color:
            parts.append(f"Color: {variant.color}")

        return ", ".join(parts) or None

    @staticmethod
    def _normalize_payment_method(
        payment_method: PaymentMethod | str | None,
    ) -> PaymentMethod:
        """Return a valid payment method, defaulting to on_delivery."""
        if payment_method is None:
            return PaymentMethod.ON_DELIVERY

        if isinstance(payment_method, PaymentMethod):
            return payment_method

        try:
            return PaymentMethod(payment_method)
        except ValueError as exc:
            allowed = ", ".join(method.value for method in PaymentMethod)
            raise ValueError(
                f"Invalid payment method. Allowed values: {allowed}."
            ) from exc
    
    def preview_checkout(
        self,
        customer_id: UUID,
        shipping_address: dict[str, Any],
        shipping_fee: Decimal,
        payment_method: PaymentMethod | str | None = PaymentMethod.ON_DELIVERY,
    ) -> CheckoutPreview:
        """Build a read-only checkout preview for a trusted customer.

        This method does not create an order, modify the cart, or commit.
        Demo prices and stock are flagged for verification.
        """
        self._validate_shipping_fee(shipping_fee)

        address = ShippingAddressSchema.model_validate(shipping_address)
        normalized_payment_method = self._normalize_payment_method(
            payment_method
        )

        cart = self.cart_repository.get_active_cart_for_customer(
            customer_id
        )

        if cart is None:
            raise CartNotFoundError("No active cart was found.")

        if not cart.items:
            raise EmptyCartError(
                "Cannot prepare checkout for an empty cart."
            )

        preview_items: list[CheckoutItemPreview] = []
        subtotal = Decimal("0.00")
        requires_price_verification = False
        requires_stock_verification = False

        for item in cart.items:
            variant = item.variant

            if (
                variant is None
                or not variant.is_active
                or variant.product is None
                or variant.product.status != "active"
            ):
                raise VariantUnavailableError(
                    "A product in the cart is no longer available."
                )

            if item.quantity < 1:
                raise EmptyCartError(
                    "Every checkout item must have a positive quantity."
                )

            if variant.price_is_demo:
                requires_price_verification = True

            if variant.stock_is_demo:
                requires_stock_verification = True
            elif item.quantity > variant.stock_quantity:
                raise DemoCatalogDataError(
                    "A requested quantity exceeds verified stock."
                )

            unit_price = self._money(Decimal(variant.price))

            if not unit_price.is_finite() or unit_price < 0:
                raise DemoCatalogDataError(
                    "A valid product price is required for checkout."
                )

            line_total = self._money(unit_price * item.quantity)
            subtotal += line_total

            preview_items.append(
                CheckoutItemPreview(
                    variant_id=item.variant_id,
                    product_name=variant.product.name,
                    sku=variant.sku,
                    variant_description=self._variant_description(variant),
                    quantity=item.quantity,
                    unit_price=unit_price,
                    line_total=line_total,
                )
            )

        subtotal = self._money(subtotal)
        shipping_fee = self._money(shipping_fee)
        total = self._money(subtotal + shipping_fee)

        return CheckoutPreview(
            items=preview_items,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total=total,
            shipping_address=address,
            payment_method=CheckoutPaymentMethod(
                normalized_payment_method.value
            ),
            requires_price_verification=requires_price_verification,
            requires_stock_verification=requires_stock_verification,
        )

    def create_order_from_cart(
        self,
        customer_id: UUID,
        shipping_address: dict[str, Any],
        shipping_fee: Decimal,
        payment_method: PaymentMethod | str | None = PaymentMethod.ON_DELIVERY,
        *,
        confirmed: bool = False,
    ) -> Order:
        """Create an order and convert its cart in one transaction.

        Only a trusted application flow should call this method after
        explicit checkout confirmation. Do not expose the `confirmed`
        argument directly as an LLM-controlled tool parameter.
        """
        if not confirmed:
            raise CheckoutNotConfirmedError(
                "The customer must confirm checkout before order creation."
            )

        self._validate_shipping_fee(shipping_fee)

        if not shipping_address:
            raise ValueError("A shipping address is required.")

        # Validate the enum before starting database changes.
        normalized_payment_method = self._normalize_payment_method(
            payment_method
        )

        try:
            cart = self.cart_repository.get_active_cart_for_customer(
                customer_id
            )

            if cart is None:
                raise CartNotFoundError("No active cart was found.")

            self._validate_cart(cart)

            subtotal = self._money(
                sum(
                    (
                        self._money(item.variant.price) * item.quantity
                        for item in cart.items
                    ),
                    Decimal("0.00"),
                )
            )

            shipping_fee = self._money(shipping_fee)
            total = self._money(subtotal + shipping_fee)

            order = Order(
                order_number=f"ORD-{uuid4().hex[:12].upper()}",
                customer_id=customer_id,
                status=OrderStatus.PENDING,
                payment_status=PaymentStatus.UNPAID,
                subtotal=subtotal,
                shipping_fee=shipping_fee,
                total=total,
                shipping_address=shipping_address,
                payment_method=normalized_payment_method,
            )

            self.order_repository.create(order)

            order_items = [
                OrderItem(
                    order_id=order.id,
                    variant_id=item.variant_id,
                    product_name=item.variant.product.name,
                    sku=item.variant.sku,
                    variant_description=self._variant_description(
                        item.variant
                    ),
                    quantity=item.quantity,
                    unit_price=self._money(item.variant.price),
                    line_total=self._money(
                        self._money(item.variant.price) * item.quantity
                    ),
                )
                for item in cart.items
            ]

            self.order_repository.add_items(order_items)

            # The order, its items, and cart conversion share one transaction.
            cart.status = "converted"

            self.db.commit()

        except Exception:
            self.db.rollback()
            raise

        # Reload after commit so callers receive the persisted order and items.
        # This is deliberately outside the transaction's exception handler:
        # a reload failure cannot undo an order that has already been committed.
        saved_order = self.order_repository.get_by_id(
            order.id,
            customer_id,
        )

        if saved_order is None:
            raise OrderNotFoundError(
                "The order was created but could not be reloaded."
            )

        return saved_order

    def create_order_with_invoice(
        self,
        customer_id: UUID,
        shipping_address: dict[str, Any],
        shipping_fee: Decimal,
        payment_method: PaymentMethod | str | None = PaymentMethod.ON_DELIVERY,
        *,
        confirmed: bool = False,
        invoice_service: InvoiceService | None = None,
    ) -> CheckoutResult:
        """Create an order, then generate its invoice PDF.

        Invoice failure does not undo a successfully committed order.
        """
        selected_invoice_service = invoice_service or self.invoice_service

        if selected_invoice_service is None:
            raise ValueError(
                "An InvoiceService must be provided or configured "
                "before creating an order with an invoice."
            )

        order = self.create_order_from_cart(
            customer_id=customer_id,
            shipping_address=shipping_address,
            shipping_fee=shipping_fee,
            payment_method=payment_method,
            confirmed=confirmed,
        )

        try:
            invoice_pdf = selected_invoice_service.generate_invoice_pdf(
                order_id=order.id,
                customer_id=customer_id,
            )
        except Exception:
            logger.exception(
                "Order %s was created, but invoice generation failed.",
                order.order_number,
            )
            return CheckoutResult(
                order=order,
                invoice_pdf=None,
                invoice_error="Invoice generation failed.",
            )

        return CheckoutResult(
            order=order,
            invoice_pdf=invoice_pdf,
        )

    def get_order(
        self,
        order_id: UUID,
        customer_id: UUID,
    ) -> Order:
        order = self.order_repository.get_by_id(
            order_id,
            customer_id,
        )

        if order is None:
            raise OrderNotFoundError("Order not found.")

        return order

    def get_order_by_number(
        self,
        order_number: str,
        customer_id: UUID,
    ) -> Order:
        order = self.order_repository.get_by_order_number(
            order_number,
            customer_id,
        )

        if order is None:
            raise OrderNotFoundError("Order not found.")

        return order

    def list_orders(
        self,
        customer_id: UUID,
        limit: int = 10,
    ) -> list[Order]:
        if not 1 <= limit <= 50:
            raise ValueError("Limit must be between 1 and 50.")

        return self.order_repository.list_for_customer(
            customer_id,
            limit=limit,
        )
