from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List


@dataclass
class NotFound:
    """
    Resolver recognizes this question, but while resolving determined it does not exist
    """

    pass


class Resolver(ABC):
    @abstractmethod
    def supports_handling(self) -> List[type]:
        pass

    @abstractmethod
    async def resolve(self, question):
        pass
