from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class NotFound:
    """
    Resolver recognizes this question, but while resolving determined it does not exist
    """


class SupportsResolve(Protocol):
    async def resolve(self, question: Any) -> Any:
        pass
