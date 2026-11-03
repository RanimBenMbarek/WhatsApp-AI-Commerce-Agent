
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import select

class CustomerRepository:
    """Database access for customers."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_whatsapp_id(
        self,
        whatsapp_id: str,
    ) -> Customer | None:
        normalized_id = whatsapp_id.strip()

        if not normalized_id:
            return None

        statement = select(Customer).where(
            Customer.whatsapp_id == normalized_id
        )
        return self.db.scalar(statement)
    
    def get_or_create(
        self,
        whatsapp_id: str,
        name: str | None = None,
    ) -> Customer:
    
        normalized_whatsapp_id = whatsapp_id.strip()

        statement = (
            insert(Customer)
            .values(
                whatsapp_id=normalized_whatsapp_id,
                name=name,
            )
            .on_conflict_do_nothing(
                index_elements=[Customer.whatsapp_id]
            )
            .returning(Customer.id)
        )

        customer_id = self.db.scalar(statement)

        if customer_id is not None:
            return self.db.get(Customer, customer_id)

        return self.db.scalar(
            select(Customer).where(
                Customer.whatsapp_id == normalized_whatsapp_id
            )
        )