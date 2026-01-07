from dataclasses import Field, dataclass
from typing import Any, ClassVar, Protocol, runtime_checkable


@dataclass(frozen=True)
class DoesNotExist[T: Repo]:
    """
    Resolver recognizes this question, but while resolving determined it does not exist
    """

    # womp womp, we can't really retrieve the value of T at runtime so gotta still pass
    # that in.
    # FIXME: See if we can enforce somehow that kind is also a `Repo`
    kind: type
    message: str


@dataclass(frozen=True)
class Exists[T: Repo]:
    repo: T


@dataclass(frozen=True)
class MaybeExists[T: Repo]:
    repo: T


@runtime_checkable
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

    # Must also be a dataclass
    __dataclass_fields__: ClassVar[dict[str, Field[Any]]]


class SupportsResolve(Protocol):
    async def resolve(
        self, question: Any
    ) -> Exists | DoesNotExist | MaybeExists | None:
        pass
