import inspect
import types
import typing
from logging import Logger, getLogger
from pathlib import Path
from typing import Optional

from repoproviders.fetchers.ckan import CKANFetcher
from repoproviders.fetchers.hydroshare import HydroshareFetcher
from repoproviders.fetchers.rclone import GoogleDriveFolderFetcher
from repoproviders.fetchers.zenodo import ZenodoFetcher
from repoproviders.resolvers.base import Repo

from .base import SupportsFetch
from .dataverse import DataverseFetcher
from .figshare import FigshareFetcher
from .git import GitHubActionArtifactFetcher, ImmutableGitFetcher

ALL_FETCHERS: list[SupportsFetch] = [
    ImmutableGitFetcher(),
    DataverseFetcher(),
    GitHubActionArtifactFetcher(),
    FigshareFetcher(),
    ZenodoFetcher(),
    GoogleDriveFolderFetcher(),
    HydroshareFetcher(),
    CKANFetcher(),
]

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


async def fetch(question: Repo, output_dir: Path, log: Optional[Logger] = None):
    if log is None:
        # Use default named logger
        log = getLogger("repoproviders")
    fetcher = FETCHER_BY_TYPE[type(question)]

    await fetcher.fetch(question, output_dir, log)
