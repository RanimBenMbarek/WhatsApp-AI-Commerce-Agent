from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.repositories.customer_repository import CustomerRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.whatsapp_webhook_parser import IncomingWhatsAppMessage


@dataclass(frozen=True)
class IncomingMessageResult:
    customer_id: UUID
    conversation_id: UUID
    message_id: UUID | None
    is_duplicate: bool


class IncomingMessageService:
    def __init__(self, db: Session):
        self.db = db
        self.customer_repository = CustomerRepository(db)
        self.conversation_repository = ConversationRepository(db)
        self.message_repository = MessageRepository(db)

    def process(self, message: IncomingWhatsAppMessage) -> IncomingMessageResult:
        try:
            customer = self.customer_repository.get_or_create(
                whatsapp_id=message.sender_whatsapp_id,
                name=message.contact_name,
            )

            conversation = self.conversation_repository.get_open_for_customer(
                customer_id=customer.id,
            )

            if conversation is None:
                conversation = self.conversation_repository.create(
                    customer_id=customer.id,
                )

            message_id = self.message_repository.add_inbound_if_new(
                conversation_id=conversation.id,
                external_message_id=message.message_id,
                content=message.text,
                metadata={"contact_name": message.contact_name},
            )

            is_duplicate = message_id is None

            if not is_duplicate:
                self.conversation_repository.update_activity(conversation.id)

            self.db.commit()

            return IncomingMessageResult(
                customer_id=customer.id,
                conversation_id=conversation.id,
                message_id=message_id,
                is_duplicate=is_duplicate,
            )

        except Exception:
            self.db.rollback()
            raise


def process_incoming_message(
    message: IncomingWhatsAppMessage,
) -> IncomingMessageResult:
    """Run one incoming-message transaction with its own database session."""

    with SessionLocal() as db:
        return IncomingMessageService(db).process(message)