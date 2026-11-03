
import hashlib
import hmac

from fastapi import APIRouter, HTTPException, Query, Request, Response, status
from starlette.concurrency import run_in_threadpool
from app.services.commerce_agent_service import CommerceAgentService
from app.services.incoming_message_service import process_incoming_message
from app.services.incoming_message_service import IncomingMessageService
from app.services.outgoing_message_service import OutgoingMessageService
from app.services.whatsapp_messaging_service import WhatsAppMessagingService
from app.services.whatsapp_webhook_parser import parse_incoming_messages

router = APIRouter(prefix="/webhooks/whatsapp", tags=["WhatsApp"])

import logging

logger = logging.getLogger(__name__)

@router.get("")
async def verify_whatsapp_webhook(
    request: Request,
    mode: str | None = Query(default=None, alias="hub.mode"),
    verify_token: str | None = Query(default=None, alias="hub.verify_token"),
    challenge: str | None = Query(default=None, alias="hub.challenge"),
) -> Response:
    """Verify the WhatsApp webhook subscription with Meta."""

    settings = request.app.state.settings
    print("Webhook mode:", repr(mode))
    print("Verify token provided:", verify_token is not None)
    print("Verify token matches:", verify_token == settings.whatsapp_verify_token)
    print("Challenge provided:", challenge is not None)

    if (
        mode == "subscribe"
        and verify_token == settings.whatsapp_verify_token
        and challenge is not None
    ):
        return Response(
            content=challenge,
            media_type="text/plain",
            status_code=status.HTTP_200_OK,
        )

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Webhook verification failed.",
    )


@router.post("")
async def receive_whatsapp_webhook(request: Request) -> dict:
    """Receive, process, and respond to incoming WhatsApp messages."""

    settings = request.app.state.settings
    app_secret = settings.meta_app_secret
    signature = request.headers.get("X-Hub-Signature-256")

    # 1. Verify Meta's signature.
    if not app_secret or not signature:
        logger.warning(
            "WhatsApp webhook rejected: app_secret_configured=%s, "
            "signature_header_present=%s",
            bool(app_secret),
            bool(signature),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature.",
        )

    body = await request.body()

    expected_signature = "sha256=" + hmac.new(
        key=app_secret.encode("utf-8"),
        msg=body,
        digestmod=hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected_signature, signature):
        logger.warning(
            "WhatsApp webhook signature mismatch: body_length=%s, "
            "signature_header_present=%s",
            len(body),
            True,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid webhook signature.",
        )

    logger.info(
        "WhatsApp webhook signature verified: body_length=%s",
        len(body),
    )
    # 2. Parse the JSON payload.
    try:
        payload = await request.json()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload.",
        ) from None

    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid webhook payload.",
        )

    # 3. Extract incoming text messages.
    incoming_messages = parse_incoming_messages(payload)

    # 4. Prepare services.
    agent_service = CommerceAgentService(
        agent=request.app.state.commerce_agent,
    )

    whatsapp_service = WhatsAppMessagingService(settings)

    outgoing_service = OutgoingMessageService(
        whatsapp_service=whatsapp_service,
    )

    messages_saved = 0
    duplicates_ignored = 0
    replies_sent = 0

    # 5. Process each incoming message.
    for message in incoming_messages:

        # Synchronous database work in a worker thread.
        result = await run_in_threadpool(
            process_incoming_message,
            message,
        )

        if result.is_duplicate:
            duplicates_ignored += 1
            continue

        messages_saved += 1

        # 6. Generate a reply using the shared agent.
        # agent.invoke() is synchronous, so run it in a worker thread.
        reply = await run_in_threadpool(
            agent_service.generate_reply,
            result.customer_id,
            result.conversation_id,
            message.text,
        )

        # 7. Send the reply asynchronously.
        # The outgoing service handles its own DB save in a worker thread.
        await outgoing_service.send_and_save(
            conversation_id=result.conversation_id,
            recipient=message.sender_whatsapp_id,
            message_text=reply,
        )

        replies_sent += 1
    logger.info(
        "Webhook processing result: received=%s, saved=%s, "
        "duplicates=%s, replies=%s",
        len(incoming_messages),
        messages_saved,
        duplicates_ignored,
        replies_sent,
    )

    return {
        "status": "received",
        "messages_received": len(incoming_messages),
        "messages_saved": messages_saved,
        "duplicates_ignored": duplicates_ignored,
        "replies_sent": replies_sent,
    }