
from uuid import UUID

from app.agents.thread_config import build_agent_config


class CommerceAgentService:
    """Invoke the shared commerce agent for a specific customer."""

    def __init__(self, agent):
        self.agent = agent

    def generate_reply(
        self,
        customer_id: UUID,
        conversation_id: UUID,
        message_text: str,
    ) -> str:
        """Generate a reply using trusted customer and conversation context."""

        result = self.agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": message_text,
                    }
                ],
            },
            config=build_agent_config(str(conversation_id)),
            context={
                "customer_id": customer_id,
            },
        )

        reply = result["messages"][-1].content

        if not isinstance(reply, str):
            raise ValueError("Agent returned a non-text response.")

        return reply
 