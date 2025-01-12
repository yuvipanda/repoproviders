import json
from pathlib import Path
from typing import Callable

from yarl import URL

from .base import MaybeExists, Repo
from .urls import (
    DataverseURL,
    Doi,
    FigshareInstallation,
    FigshareURL,
    GitHubURL,
    ZenodoURL,
)


class WellKnownProvidersResolver:
    def detect_github(self, question: URL) -> GitHubURL | None:
        # git+<scheme> urls are handled by a different resolver
        if question.scheme not in ("http", "https") or (
            question.host != "github.com" and question.host != "www.github.com"
        ):
            # TODO: Allow configuring for GitHub enterprise
            return None
        else:
            return GitHubURL(URL("https://github.com"), question)

    def detect_zenodo(self, question: URL) -> ZenodoURL | None:
        KNOWN_INSTALLATIONS = [
            URL("https://sandbox.zenodo.org/"),
            URL("https://zenodo.org/"),
            URL("https://data.caltech.edu/"),
        ]
        installation = next(
            (
                installation
                for installation in KNOWN_INSTALLATIONS
                # Intentionally don't check for scheme validity, to support interchangeable http and https URLs
                if installation.host == question.host
                # Check for base URL, to support installations on base URL other than /
                and question.path.startswith(installation.path)
                and (
                    # After the base URL, the URL structure should start with either record or records
                    question.path[len(installation.path) :].startswith("record/")
                    or question.path[len(installation.path) :].startswith("records/")
                    or question.path[len(installation.path) :].startswith("doi/")
                )
            ),
            None,
        )
        if installation is None:
            return None

        return ZenodoURL(installation, question)

    def detect_dataverse(self, question: URL) -> DataverseURL | None:

        if not hasattr(self, "_dataverse_installation_urls"):
            # Get a list of installation URLs for known dataverse installations
            data_file = Path(__file__).parent / "dataverse.json"
            with open(data_file) as fp:
                installations = json.load(fp)["installations"]

            # Parse all the URLs of installations once, so we can quickly use them for validating URLs passed in
            # TODO: Use a better datastructure here (like a trie?)
            self._dataverse_installation_urls = [URL(i["url"]) for i in installations]

        # Check if URL is under one of the installation URLs we have.
        installation = next(
            (
                installation
                for installation in self._dataverse_installation_urls
                # Intentionally don't check for scheme validity, to support interchangeable http and https URLs
                if installation.host == question.host
                and question.path.startswith(installation.path)
            ),
            None,
        )
        if installation is None:
            return None
        else:
            return DataverseURL(installation, question)

    def detect_figshare(self, question: URL) -> FigshareURL | None:
        KNOWN_INSTALLATIONS = [
            FigshareInstallation(
                URL("https://figshare.com/"), URL("https://api.figshare.com/v2/")
            )
        ]

        installation = next(
            (
                installation
                for installation in KNOWN_INSTALLATIONS
                # Intentionally don't check for scheme validity, to support interchangeable http and https URLs
                if installation.url.host == question.host
                # Check for base URL, to support installations on base URL other than /
                and question.path.startswith(installation.url.path)
                and (
                    # After the base URL, the URL structure should start with either record or records
                    question.path[len(installation.url.path) :].startswith("articles/")
                    or question.path[len(installation.url.path) :].startswith(
                        "account/articles/"
                    )
                )
            ),
            None,
        )
        if installation is None:
            return None

        return FigshareURL(installation, question)

    async def resolve(self, question: URL | Doi) -> MaybeExists[Repo] | None:
        # These detectors are *intentionally* not async, as they should not be doing any
        # network calls
        detectors: list[Callable[[URL], Repo | None]] = [
            self.detect_github,
            self.detect_dataverse,
            self.detect_zenodo,
            self.detect_figshare,
        ]

        match question:
            case URL():
                url = question
            case Doi(doi_url):
                url = doi_url

        for d in detectors:
            maybe_answer = d(url)
            if maybe_answer is not None:
                return MaybeExists(maybe_answer)

        return None
