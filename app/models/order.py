
from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from uuid import UUID

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Numeric,
    Text,
    Enum as SAEnum,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class OrderStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class PaymentStatus(str, PyEnum):
    UNPAID = "unpaid"
    PAID = "paid"
    FAILED = "failed"


class PaymentMethod(str, PyEnum):
    ON_DELIVERY = "on_delivery"
    BY_CARD = "by_card"


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    order_number: Mapped[str] = mapped_column(
        Text, nullable=False, unique=True
    )

    customer_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id"),
        nullable=False,
    )

    status: Mapped[OrderStatus] = mapped_column(
        SAEnum(
            OrderStatus,
            name="order_status",
            native_enum=False,
            values_callable=lambda cls: [item.value for item in cls],
        ),
        nullable=False,
        default=OrderStatus.PENDING,
        server_default=text("'pending'"),
    )

    payment_status: Mapped[PaymentStatus] = mapped_column(
        SAEnum(
            PaymentStatus,
            name="payment_status_enum",
            native_enum=False,
            values_callable=lambda cls: [item.value for item in cls],
        ),
        nullable=False,
        default=PaymentStatus.UNPAID,
        server_default=text("'unpaid'"),
    )

    subtotal: Mapped[Decimal] = mapped_column(
        Numeric, nullable=False
    )

    shipping_fee: Mapped[Decimal] = mapped_column(
        Numeric,
        nullable=False,
        server_default=text("0"),
    )

    total: Mapped[Decimal] = mapped_column(
        Numeric, nullable=False
    )

    shipping_address: Mapped[dict] = mapped_column(
        JSONB, nullable=False
    )

    payment_method: Mapped[PaymentMethod | None] = mapped_column(
        SAEnum(
            PaymentMethod,
            name="payment_method_enum",
            native_enum=False,
            values_callable=lambda cls: [item.value for item in cls],
        ),
        nullable=True,
        default=PaymentMethod.ON_DELIVERY,
        server_default=text("'on_delivery'"),
    )

    carrier: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    tracking_number: Mapped[str | None] = mapped_column(
        Text, nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    shipped_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order",
    )
