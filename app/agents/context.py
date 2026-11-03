from typing import TypedDict
from uuid import UUID


class CommerceAgentContext(TypedDict):
    customer_id: UUID | None