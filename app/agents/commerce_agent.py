
from uuid import UUID

from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import InMemorySaver

from app.agents.context import CommerceAgentContext
from app.agents.prompts import SYSTEM_PROMPT
from app.core.config import get_settings
from app.tools.cart_tools import create_cart_tools
from app.tools.product_availability import create_product_availability_tool
from app.tools.product_search import create_product_search_tool


def create_commerce_agent(
    checkpointer=None,
):
    """Build the commerce agent.

    Cart tools are added only when trusted application code supplies
    a customer ID. Never obtain this ID from the LLM.
    """
    settings = get_settings()

    if not settings.openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY must be configured before creating the agent."
        )

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        api_key=settings.openai_api_key,
        temperature=0.0,
    )
    tools = [
        create_product_search_tool(),
        create_product_availability_tool(),
        *create_cart_tools(),
    ]

    if checkpointer is None:
        checkpointer = InMemorySaver()

    return create_agent(
        model=llm,
        tools=tools,
        system_prompt=SYSTEM_PROMPT,
        checkpointer=checkpointer,
        context_schema=CommerceAgentContext,
    )
