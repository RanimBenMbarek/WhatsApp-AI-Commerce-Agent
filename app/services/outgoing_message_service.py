from uuid import UUID

from starlette.concurrency import run_in_threadpool

from app.db.session import SessionLocal
from app.repositories.message_repository import MessageRepository
from app.services.whatsapp_messaging_service import WhatsAppMessagingService


class OutgoingMessageService:
    """Send WhatsApp replies and persist them."""

    def __init__(
        self,
        whatsapp_service: WhatsAppMessagingService,
    ):
        self.whatsapp_service = whatsapp_service

    async def send_and_save(
        self,
        conversation_id: UUID,
        recipient: str,
        message_text: str,
    ) -> UUID:
        """Send a WhatsApp reply, then save its message record."""

        response = await self.whatsapp_service.send_text_message(
            recipient=recipient,
            message=message_text,
        )

        messages = response.get("messages", [])

        if not messages or not messages[0].get("id"):
            raise ValueError(
                "WhatsApp API response does not contain a message ID."
            )

        external_message_id = messages[0]["id"]

        return await run_in_threadpool(
            self._save_outgoing_message,
            conversation_id,
            external_message_id,
            message_text,
            response,
        )

    @staticmethod
    def _save_outgoing_message(
        conversation_id: UUID,
        external_message_id: str,
        message_text: str,
        response: dict,
    ) -> UUID:
        """Persist an outgoing message using a thread-local session."""

        with SessionLocal() as db:
            try:
                message_repository = MessageRepository(db)

                message_id = message_repository.add_outbound_if_new(
                    conversation_id=conversation_id,
                    external_message_id=external_message_id,
                    content=message_text,
                    metadata={"whatsapp_response": response},
                )

                if message_id is None:
                    raise ValueError(
                        "Outbound WhatsApp message already exists in the database."
                    )

                db.commit()
                return message_id

            except Exception:
                db.rollback()
                raise