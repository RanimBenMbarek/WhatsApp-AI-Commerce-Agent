
from dataclasses import dataclass


@dataclass(frozen=True)
class IncomingWhatsAppMessage:
    message_id: str
    sender_whatsapp_id: str
    text: str
    contact_name: str | None = None


def parse_incoming_messages(
    payload: dict,
) -> list[IncomingWhatsAppMessage]:
    """Extract incoming text messages from a Meta WhatsApp webhook."""

    parsed_messages = []

    entries = payload.get("entry", [])

    if not isinstance(entries, list):
        return parsed_messages

    for entry in entries:
        if not isinstance(entry, dict):
            continue

        changes = entry.get("changes", [])

        if not isinstance(changes, list):
            continue

        for change in changes:
            if not isinstance(change, dict):
                continue

            if change.get("field") != "messages":
                continue

            value = change.get("value", {})

            if not isinstance(value, dict):
                continue

            contact_names = {}

            contacts = value.get("contacts", [])

            if isinstance(contacts, list):
                for contact in contacts:
                    if not isinstance(contact, dict):
                        continue

                    whatsapp_id = contact.get("wa_id")
                    profile = contact.get("profile", {})

                    if (
                        isinstance(whatsapp_id, str)
                        and isinstance(profile, dict)
                        and isinstance(profile.get("name"), str)
                    ):
                        contact_names[whatsapp_id] = profile["name"]

            messages = value.get("messages", [])

            if not isinstance(messages, list):
                continue

            for message in messages:
                if not isinstance(message, dict):
                    continue

                if message.get("type") != "text":
                    continue

                message_id = message.get("id")
                sender_id = message.get("from")
                text_data = message.get("text", {})

                if not isinstance(text_data, dict):
                    continue

                message_text = text_data.get("body")

                if not all(
                    isinstance(item, str) and item.strip()
                    for item in (message_id, sender_id, message_text)
                ):
                    continue

                parsed_messages.append(
                    IncomingWhatsAppMessage(
                        message_id=message_id,
                        sender_whatsapp_id=sender_id,
                        text=message_text,
                        contact_name=contact_names.get(sender_id),
                    )
                )

    return parsed_messages
