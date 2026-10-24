
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.order import Order
from app.models.order_item import OrderItem

class OrderRepository:
    """Database operations for orders and their items."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def create(self, order: Order) -> Order:
        """Stage a new order for insertion."""
        self.session.add(order)
        self.session.flush()
        return order

    def get_by_id(
        self,
        order_id: UUID,
        customer_id: UUID,
    ) -> Order | None:
        """Fetch an order belonging to the specified customer."""
        statement = (
            select(Order)
            .where(
                Order.id == order_id,
                Order.customer_id == customer_id,
            )
            .options(selectinload(Order.items))
        )
        return self.session.scalars(statement).first()

    def get_by_order_number(
        self,
        order_number: str,
        customer_id: UUID,
    ) -> Order | None:
        """Fetch an order by its number, scoped to its customer."""
        statement = (
            select(Order)
            .where(
                Order.order_number == order_number,
                Order.customer_id == customer_id,
            )
            .options(selectinload(Order.items))
        )
        return self.session.scalars(statement).first()

    def list_for_customer(
        self,
        customer_id: UUID,
        limit: int = 10,
    ) -> list[Order]:
        """Return a customer's most recent orders."""
        statement = (
            select(Order)
            .where(Order.customer_id == customer_id)
            .options(selectinload(Order.items))
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(self.session.scalars(statement).all())

    def add_items(self, items: list[OrderItem]) -> None:
        """Stage order items for insertion."""
        self.session.add_all(items)
        self.session.flush()
