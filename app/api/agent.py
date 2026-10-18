from fastapi import APIRouter

from app.schemas.agent import AgentChatRequest, AgentChatResponse, AgentChatResponse


router = APIRouter(prefix="/agent", tags=["Agent"])

@router.post("/chat", response_model=AgentChatResponse)
def chat_with_agent(
    payload: AgentChatRequest,
    request: AgentChatRequest
) -> AgentChatResponse:
    """
    Endpoint to chat with the agent.
    """
    agent = request.app.state.commerce_agent
    
    try:
        result = agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": payload.message,
                    }
                ]
            }
        )
        reply = result["messages"][-1]["content"]
    except Exception as e:
        print(f"Error occurred while invoking agent: {e}")
        reply = "Sorry, I encountered an error while processing your request."
    return AgentChatResponse(reply=reply)