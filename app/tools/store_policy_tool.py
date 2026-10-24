
from typing import Literal

from langchain.tools import tool

from app.services.policy_service import StorePolicyService


def create_store_policy_tools(
    policy_service: StorePolicyService | None = None,
):
    service = policy_service or StorePolicyService()

    @tool
    def get_store_policy(
        topic: Literal[
            "delivery",
            "returns",
            "refunds",
            "payments",
            "cancellations",
        ],
    ) -> str:
        """Retrieve the store's official policy for a topic.

        Use this tool to answer questions about delivery, returns,
        refunds, payment methods, or cancellations.

        Only communicate policy details returned as configured.
        If the policy is not configured or unavailable, explain that
        the store has not provided confirmed information and recommend
        contacting store support. Never invent policy details.
        """

        result = service.get_policy(topic)

        if result["status"] == "configured":
            return (
                f"Official {topic} policy: {result['answer']}"
            )

        if result["status"] == "not_configured":
            return (
                f"The store's {topic} policy has not been configured. "
                "Do not guess. Explain that the customer should contact "
                "store support for confirmation."
            )

        if result["status"] == "unsupported_topic":
            return "This policy topic is not supported."

        return (
            "The store policy source is currently unavailable. "
            "Do not guess; recommend contacting store support."
        )

    return [get_store_policy]
