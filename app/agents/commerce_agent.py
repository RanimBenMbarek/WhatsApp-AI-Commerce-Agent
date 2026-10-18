from langchain.agents import create_agent
from langchain_openai import ChatOpenAI

from app.agents.prompts import SYSTEM_PROMPT
from app.core.config import get_settings
from app.tools.product_search import create_product_search_tool


def create_commerce_agent()  :
    """Create the fashion and beauty customer-service agent."""
    
    settings = get_settings()

    if not settings.openai_api_key:
        raise ValueError(
            "OPENAI_API_KEY must be configured before creating the agent."
    )
    

    llm = ChatOpenAI(
        model_name="gpt-4o-mini",
        temperature=0.0,
    )
    product_search_tool = create_product_search_tool()

    agent = create_agent(
        model=llm, 
        tools=[product_search_tool],
        system_prompt=SYSTEM_PROMPT,
    )

    return agent