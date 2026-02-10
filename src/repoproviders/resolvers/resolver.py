import inspect
import types
import typing
from typing import Any

from yarl import URL

from repoproviders.resolvers.feature_detect import FeatureDetectResolver

from .base import DoesNotExist, Exists, MaybeExists, SupportsResolve
from .doi import (
    DataverseResolver,
    DoiResolver,
    FigshareResolver,
    ImmutableFigshareResolver,
    ZenodoResolver,
)
from .git import (
    GistResolver,
    GitHubPRResolver,
    GitHubResolver,
    GitLabResolver,
    GitUrlResolver,
    ImmutableGitResolver,
)
from .rclone import GoogleDriveFolderResolver
from .wellknown import WellKnownProvidersResolver

ALL_RESOLVERS: list[SupportsResolve] = [
    WellKnownProvidersResolver(),
    GitHubResolver(),
    GitHubPRResolver(),
    GistResolver(),
    GoogleDriveFolderResolver(),
    GitUrlResolver(),
    GitLabResolver(),
    DoiResolver(),
    ZenodoResolver(),
    FigshareResolver(),
    ImmutableFigshareResolver(),
    DataverseResolver(),
    ImmutableGitResolver(),
    FeatureDetectResolver(),
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


async def resolve(
    question: str | Any, recursive: bool
) -> list[Exists | MaybeExists | DoesNotExist] | None:
    if isinstance(question, str):
        question = URL(question)

    answers: list[Exists | MaybeExists | DoesNotExist] = []
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
                # Break out of the for after we find an answer in each round
                break

        if recursive:
            # If we want a recursive answer, we have to continue iterating
            match resp:
                case DoesNotExist():
                    # Some resolver detected this but we have confirmed it does not exist
                    break
                case Exists(repo):
                    # TODO: Should an "Exists" be further resolved, or does it always indicate an end?
                    question = repo
                case MaybeExists(repo):
                    question = repo
                case None:
                    # No answer was found this round so we are done
                    break
                # We *did* find an answer this round, so we should continue and see if we find more
            resp = None
        else:
            # We are not recursive, so we are done after 1 round regardless
            break

    return answers
