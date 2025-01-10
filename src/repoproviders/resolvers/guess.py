import aiohttp
from yarl import URL

from .base import Exists
from .git import Git


class GuessResolver:
    """
    Use heuristics to guess what kinda thing this is.

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

    # async def is_dataverse(self, session: aiohttp.ClientSession, url: URL) -> Exists[DataverseDataset] | None:
    #     """
    #     Check if a given URL is under a dataverse install
    #     """

    #     # Make an API call to check if this is a dataverse instance
    #     # https://guides.dataverse.org/en/latest/api/native-api.html#show-dataverse-software-version-and-build-number
    #     # FIXME: This assumes that the dataverse instance is hosted at the root of the server,
    #     # without any other path prefix
    #     api_url = url.with_path("/api/info/version")
    #     resp = await session.get(api_url)

    #     if resp.status == 200:
    #         try:
    #             version_data = await resp.json()
    #             if version_data.get("status") == "OK" and "version" in version_data.get("data", {}):
    #             if "status" in version_data and
    #         except:
    #             return None

    async def resolve(self, question: URL) -> Exists[Git] | None:
        if question.scheme not in ("http", "https"):
            return None

        guessers = (
            self.is_git_repo,
            # self.is_dataverse
        )

        async with aiohttp.ClientSession() as session:
            for g in guessers:
                maybe_answer = await g(session, question)
                if maybe_answer is not None:
                    return maybe_answer
