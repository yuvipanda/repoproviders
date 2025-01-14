import aiohttp
from yarl import URL

from .base import Exists, MaybeExists
from .repos import DataverseURL, Git


class FeatureDetectResolver:
    """
    Use external network calls to detect what kinda URL this is.

    Resolver of last resort!
    """

    async def is_git_repo(
        self, session: aiohttp.ClientSession, url: URL
    ) -> Exists[Git] | None:
        """
        Return true if url is a git repository that supports the smart HTTP git protocol
        """
        # Read https://github.com/git/git/blob/master/Documentation/gitprotocol-http.txt
        # to understand the smart HTTP git protocol better.
        # Short version is that we look for a 200 response in $GIT_URL/info/refs?service=git-upload-pack
        # To determine if this is a git repo
        refs_url = url / "info/refs"
        refs_url = refs_url.with_query(service="git-upload-pack")

        resp = await session.get(refs_url)

        if resp.status == 200:
            return Exists(Git(str(url), "HEAD"))

        # Not a smart git URL
        return None

    async def is_dataverse(
        self, session: aiohttp.ClientSession, url: URL
    ) -> MaybeExists[DataverseURL] | None:
        """
        Check if a given URL is under a dataverse install
        """

        # Make an API call to check if this is a dataverse instance
        # https://guides.dataverse.org/en/latest/api/native-api.html#show-dataverse-software-version-and-build-number
        # FIXME: This assumes that the dataverse instance is hosted at the root of the server,
        # without any other path prefix
        installation = url.with_path("/").with_fragment(None).with_query(None)
        api_url = installation.with_path("/api/info/version")
        resp = await session.get(api_url)

        if resp.status == 200:
            try:
                version_data = await resp.json()
                if version_data.get("status") == "OK" and "version" in version_data.get(
                    "data", {}
                ):
                    return MaybeExists(DataverseURL(installation, url))
            except:
                pass

        return None

    async def resolve(
        self, question: URL
    ) -> Exists[Git] | MaybeExists[DataverseURL] | None:
        if question.scheme not in ("http", "https"):
            return None

        detectors = (self.is_git_repo, self.is_dataverse)

        async with aiohttp.ClientSession() as session:
            for g in detectors:
                maybe_answer = await g(session, question)
                if maybe_answer is not None:
                    return maybe_answer

        return None
