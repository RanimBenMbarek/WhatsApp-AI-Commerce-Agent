from typing import Any
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Message


class MessageRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_inbound_if_new(
        self,
        conversation_id: UUID,
        external_message_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> UUID | None:
        statement = (
            insert(Message)
            .values(
                conversation_id=conversation_id,
                external_message_id=external_message_id,
                direction="inbound",
                sender_type="customer",
                content=content,
                message_type="text",
                message_metadata=metadata or {},
            )
            .on_conflict_do_nothing(
                index_elements=[Message.external_message_id],
                index_where=text("external_message_id IS NOT NULL"),
            )
            .returning(Message.id)
        )

        return self.db.scalar(statement)

    
    def add_outbound_if_new(
        self,
        conversation_id: UUID,
        external_message_id: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> UUID | None:
        """Save an assistant message unless its external ID already exists."""

        statement = (
            insert(Message)
            .values(
                conversation_id=conversation_id,
                external_message_id=external_message_id,
                direction="outbound",
                sender_type="assistant",
                content=content,
                message_type="text",
                message_metadata=metadata or {},
            )
            .on_conflict_do_nothing(
                index_elements=[Message.external_message_id],
                index_where=text("external_message_id IS NOT NULL"),
            )
            .returning(Message.id)
        )

        return self.db.scalar(statement)
