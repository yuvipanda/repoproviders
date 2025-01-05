import inspect
import types
import typing
from typing import Any

from yarl import URL

from .base import Repo, SupportsResolve
from .doi import (
    DataverseResolver,
    DoiResolver,
    FigshareResolver,
    ImmutableFigshareResolver,
    ZenodoResolver,
)
from .git import GitHubResolver, GitUrlResolver, ImmutableGitResolver

ALL_RESOLVERS: list[SupportsResolve] = [
    GitHubResolver(),
    GitUrlResolver(),
    DoiResolver(),
    ZenodoResolver(),
    FigshareResolver(),
    ImmutableFigshareResolver(),
    DataverseResolver(),
    ImmutableGitResolver(),
]

RESOLVER_BY_TYPE: dict[type, list[SupportsResolve]] = {}
for R in ALL_RESOLVERS:
    annotations = inspect.get_annotations(R.resolve)
    supported_types = annotations["question"]
    if isinstance(supported_types, type):
        # Only supports a single type
        RESOLVER_BY_TYPE.setdefault(supported_types, []).append(R)
    elif isinstance(supported_types, types.UnionType):
        for t in typing.get_args(supported_types):
            RESOLVER_BY_TYPE.setdefault(t, []).append(R)


async def resolve(question: str | Any, recursive: bool) -> list[Repo] | None:
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
