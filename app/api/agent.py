
import logging

from fastapi import APIRouter, HTTPException, Request, status
from starlette.concurrency import run_in_threadpool

from app.agents.thread_config import build_agent_config
from app.schemas.agent import AgentChatRequest, AgentChatResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agent", tags=["Agent"])

DEV_CONVERSATION_ID = "internal-development-thread"

@router.post("/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    payload: AgentChatRequest,
    request: Request,
) -> AgentChatResponse:
    """Send a customer message to the commerce agent."""

    agent = request.app.state.commerce_agent
    config =build_agent_config(DEV_CONVERSATION_ID)

    try:

        result = await run_in_threadpool(
            agent.invoke,
            {
                "messages": [
                    {
                        "role": "user",
                        "content": payload.message,
                    }
                ],
            }, 
            config=config,
        )


        reply = result["messages"][-1].content

        if not isinstance(reply, str):
            raise ValueError("Agent returned a non-text response.")

        return AgentChatResponse(reply=reply)

    except Exception:
        logger.exception("Commerce agent failed to process a message")

        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The assistant could not process your message.",
        ) from None
