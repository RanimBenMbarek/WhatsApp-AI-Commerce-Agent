
import httpx

from app.core.config import Settings


class WhatsAppMessagingService:
    """Send messages through the WhatsApp Cloud API."""

    GRAPH_API_VERSION = "v25.0"

    def __init__(self, settings: Settings):
        self.settings = settings

    async def send_text_message(
        self,
        recipient: str,
        message: str,
    ) -> dict:
        """Send a text message to a WhatsApp recipient."""

        if not self.settings.whatsapp_access_token:
            raise ValueError("WhatsApp access token is not configured.")

        if not self.settings.whatsapp_phone_number_id:
            raise ValueError("WhatsApp phone number ID is not configured.")

        url = (
            f"https://graph.facebook.com/"
            f"{self.GRAPH_API_VERSION}/"
            f"{self.settings.whatsapp_phone_number_id}/messages"
        )

        headers = {
            "Authorization": (
                f"Bearer {self.settings.whatsapp_access_token}"
            ),
            "Content-Type": "application/json",
        }

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": recipient,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": message,
            },
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                url,
                headers=headers,
                json=payload,
            )

        if response.is_error:
            print("WhatsApp API status:", response.status_code)
            print("WhatsApp API error:", response.text)

        response.raise_for_status()
        return response.json()
