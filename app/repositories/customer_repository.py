
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Customer


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
