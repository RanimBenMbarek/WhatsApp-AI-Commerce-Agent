
import json
from pathlib import Path
from typing import Any


POLICY_FILE = (
    Path(__file__).resolve().parents[1]
    / "data"
    / "store_policies.json"
)


class StorePolicyService:
    """Read the store's configured policies."""

    def __init__(self, policy_file: Path = POLICY_FILE):
        self.policy_file = policy_file

    def get_policy(self, topic: str) -> dict[str, Any]:
        """Return a configured policy or an explicit unavailable result."""

        if topic not in {
            "delivery",
            "returns",
            "refunds",
            "payments",
            "cancellations",
        }:
            return {
                "status": "unsupported_topic",
                "answer": None,
            }

        try:
            with self.policy_file.open("r", encoding="utf-8") as file:
                policies = json.load(file)
        except (OSError, json.JSONDecodeError):
            return {
                "status": "unavailable",
                "answer": None,
            }

        policy = policies.get(topic)

        if not isinstance(policy, dict):
            return {
                "status": "not_configured",
                "answer": None,
            }

        if (
            policy.get("status") != "configured"
            or not isinstance(policy.get("answer"), str)
            or not policy["answer"].strip()
        ):
            return {
                "status": "not_configured",
                "answer": None,
            }

        return {
            "status": "configured",
            "answer": policy["answer"].strip(),
        }
