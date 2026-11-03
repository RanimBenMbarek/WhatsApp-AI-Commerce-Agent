from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy import select, update, func

from app.models import Conversation


class ConversationRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_open_for_customer(
        self,
        customer_id: UUID,
    ) -> Conversation | None:
        statement = (
            select(Conversation)
            .where(
                Conversation.customer_id == customer_id,
                Conversation.channel == "whatsapp",
                Conversation.status == "open",
            )
            .order_by(Conversation.updated_at.desc())
            .limit(1)
        )

        return self.db.scalar(statement)

    def create(self, customer_id: UUID) -> Conversation:
        conversation = Conversation(
            customer_id=customer_id,
            channel="whatsapp",
        )

        self.db.add(conversation)
        self.db.flush()

        return conversation
    def update_activity(self, conversation_id: UUID) -> None:
        statement = (
            update(Conversation)
            .where(Conversation.id == conversation_id)
            .values(updated_at=func.now())
        )

        self.db.execute(statement)