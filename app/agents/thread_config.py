
def build_agent_config(conversation_id: str) -> dict:
    """Build LangGraph configuration for a trusted conversation ID.

    The caller is responsible for verifying the conversation identity.
    This helper does not authenticate the caller.
    """
    if not isinstance(conversation_id, str) or not conversation_id.strip():
        raise ValueError("conversation_id must be a non-empty string.")

    return {
        "configurable": {
            "thread_id": conversation_id.strip(),
        }
    }
