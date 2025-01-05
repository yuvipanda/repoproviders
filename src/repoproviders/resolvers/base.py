from dataclasses import dataclass
from typing import Any, Protocol


@dataclass(frozen=True)
class NotFound:
    """
    Resolver recognizes this question, but while resolving determined it does not exist
    """

    immutable = True


class Repo(Protocol):
    """
    Represents a Repository
    """

    # Set to true if the repo is identified to be immutable. This usually means one of:
    #
    # 1. The identifier used to refer to the repo is guaranteed to not change (like with zenodo record ids)
    # 2. A version identifier is included as part of the definition (like with Figshare)
    # 3. A content identifiable hash is included as part of the definition (like with ImmutableGit)
    immutable: bool


class SupportsResolve(Protocol):
    async def resolve(self, question: Any) -> Repo | None:
        pass
