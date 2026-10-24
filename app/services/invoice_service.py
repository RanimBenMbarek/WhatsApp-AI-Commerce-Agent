
from decimal import Decimal
from uuid import UUID

from sqlalchemy.orm import Session

from app.models.customer import Customer
from app.schemas.invoice import InvoiceData, InvoiceLineItem
from app.services.invoice_pdf_service import render_invoice_pdf


class InvoiceService:
    """Build invoice data from a saved order and render its PDF."""

    def __init__(
        self,
        db: Session,
        *,
        seller_name: str,
        seller_address: str,
        seller_contact: str | None = None,
        currency: str = "EUR",
    ) -> None:
        self.db = db
        self.order_service = OrderService(db)
        self.seller_name = seller_name
        self.seller_address = seller_address
        self.seller_contact = seller_contact
        self.currency = currency

    def generate_invoice_pdf(
        self,
        order_id: UUID,
        customer_id: UUID,
    ) -> bytes:
        """Generate a PDF only for an order owned by this customer."""

        # OrderService uses a customer-scoped database query.
        order = self.order_service.get_order(
            order_id=order_id,
            customer_id=customer_id,
        )

        customer = self.db.get(Customer, order.customer_id)

        if customer is None:
            raise ValueError("The customer for this order was not found.")

        shipping_address = getattr(order, "shipping_address", None)

        if not isinstance(shipping_address, dict) or not shipping_address:
            raise ValueError(
                "The order does not contain a saved shipping address."
            )

        if not order.items:
            raise ValueError("Cannot generate an invoice for an order without items.")

        invoice_data = InvoiceData(
            invoice_number=f"INV-{order.order_number}",
            issued_at=order.created_at,
            order_number=order.order_number,
            order_status=order.status,
            payment_status=order.payment_status,
            seller_name=self.seller_name,
            seller_address=self.seller_address,
            seller_contact=self.seller_contact,
            customer_name=customer.name or "Customer",
            shipping_address=shipping_address,
            items=[
                InvoiceLineItem(
                    product_name=item.product_name,
                    sku=item.sku,
                    variant_description=item.variant_description,
                    quantity=item.quantity,
                    unit_price=Decimal(item.unit_price),
                    line_total=Decimal(item.line_total),
                )
                for item in order.items
            ],
            subtotal=Decimal(order.subtotal),
            shipping_fee=Decimal(order.shipping_fee),
            total=Decimal(order.total),
            currency=self.currency,
        )

        return render_invoice_pdf(invoice_data)
