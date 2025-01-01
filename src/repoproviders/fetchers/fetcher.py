import inspect
import types
import typing
from pathlib import Path
from typing import Any

from .base import SupportsFetch
from .dataverse import DataverseFetcher
from .git import ImmutableGitFetcher

ALL_FETCHERS: list[SupportsFetch] = [ImmutableGitFetcher(), DataverseFetcher()]

FETCHER_BY_TYPE: dict[type, SupportsFetch] = {}
for R in ALL_FETCHERS:
    annotations = inspect.get_annotations(R.fetch)
    supported_types = annotations["repo"]
    if isinstance(supported_types, type):
        # Only supports a single type
        FETCHER_BY_TYPE[supported_types] = R
    elif isinstance(supported_types, types.UnionType):
        for t in typing.get_args(supported_types):
            FETCHER_BY_TYPE[t] = R


async def fetch(question: Any, output_dir: Path):
    fetcher = FETCHER_BY_TYPE[type(question)]

    await fetcher.fetch(question, output_dir)
