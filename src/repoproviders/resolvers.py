from typing import Any, List

from yarl import URL

from .base import Resolver
from .doi import DataverseResolver, DoiResolver
from .git import GitHubResolver, ImmutableGitResolver

ALL_RESOLVERS: List[Resolver] = [
    GitHubResolver(),
    DoiResolver(),
    DataverseResolver(),
    ImmutableGitResolver(),
]

RESOLVER_BY_TYPE: dict[type, list[Resolver]] = {}
for R in ALL_RESOLVERS:
    supported_types = R.supports_handling()
    for t in supported_types:
        RESOLVER_BY_TYPE.setdefault(t, []).append(R)


async def resolve(question: str | Any, recursive: bool) -> list | None:
    if isinstance(question, str):
        question = URL(question)

    answers = []
    resp = None

    while True:
        # Get a list of applicable resolvers we can try
        applicable_resolvers = RESOLVER_BY_TYPE.get(type(question), [])

        if not applicable_resolvers:
            # No applicable resolvers found for this question type, we are done
            break

        for r in applicable_resolvers:
            resp = await r.resolve(question)
            if resp is not None:
                # We found an answer!
                answers.append(resp)
                # Break after we find an answer in each round
                break

        if recursive:
            # If we want a recursive answer, we have to continue iterating
            if resp is not None:
                # We *did* find an answer this round, so we should continue and see if we find more
                question = resp
                resp = None
            else:
                # We did *not* find an answer this round, so we are done
                break
        else:
            # We are not recursive, so we are done after 1 round regardless
            break

    return answers
