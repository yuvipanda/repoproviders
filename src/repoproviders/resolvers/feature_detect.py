from json import JSONDecodeError
from logging import Logger

import aiohttp
from yarl import URL

from .base import Exists, MaybeExists
from .repos import CKANDataset, DataverseURL, Git, GitLabURL


class FeatureDetectResolver:
    """
    Use external network calls to detect what kinda URL this is.

    Resolver of last resort!
    """

    async def is_git_repo(
        self, session: aiohttp.ClientSession, url: URL, log: Logger
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
            log.debug(f"Found git repo at {url} via 200 OK response to {refs_url}")
            return Exists(Git(str(url), "HEAD"))

        # Not a smart git URL
        return None

    async def is_dataverse(
        self, session: aiohttp.ClientSession, url: URL, log: Logger
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
                    log.debug(
                        f"Detected dataverse installation at {installation} via 200 response to {api_url}"
                    )
                    return MaybeExists(DataverseURL(installation, url))
            except:
                pass

        return None

    async def is_gitlab(
        self, session: aiohttp.ClientSession, question: URL, log: Logger
    ) -> MaybeExists[GitLabURL] | None:
        # A lot of GitLab APIs seem to require auth to hit, including the version API
        # So instead, we hit the OpenID Connect Well Known Endpoint (https://docs.gitlab.com/ee/integration/openid_connect_provider.html#settings-discovery)
        # And check for GitLab specific supported claims.
        installation = question.with_path("/").with_query(None).with_fragment(None)
        openid_config_url = installation / ".well-known/openid-configuration"

        resp = await session.get(openid_config_url)

        if resp.status != 200:
            return None

        try:
            data = await resp.json()
        except JSONDecodeError:
            return None

        if "https://gitlab.org/claims/groups/owner" in data.get("claims_supported", {}):
            log.debug(
                f"Found GitLab installation at {installation} by looking for `claims_supported` in {openid_config_url}"
            )
            return MaybeExists(GitLabURL(installation, question))
        else:
            return None

    async def is_ckan(
        self, session: aiohttp.ClientSession, question: URL, log: Logger
    ) -> MaybeExists[CKANDataset] | None:
        # If there's no "/dataset/" it's not CKAN
        if "/dataset/" not in question.path:
            return None

        # Determine the API URL, so we can make a call to the status_show endpoint

        # CKAN can be under a url prefix so we should support that
        parts = question.path.split("/")
        dataset_identifier_index = parts.index("dataset")

        # Only one segment after 'dataset', which is hte dataset id
        if len(parts) != dataset_identifier_index + 2:
            return None

        url_prefix = "/".join(parts[:dataset_identifier_index])
        base_url = question.with_path(url_prefix)
        dataset_id = parts[dataset_identifier_index + 1]

        if not dataset_id:
            # Empty dataset_id is no-go
            return None

        status_api_endpoint = base_url / "api/3/action/status_show"

        resp = await session.get(status_api_endpoint)

        # Using startswith as Content-Type can also have encoding specified
        if resp.status != 200 or not resp.headers.get("Content-Type", "").startswith(
            "application/json"
        ):
            return None

        data = await resp.json()
        ckan_version = data.get("result", {}).get("ckan_version")
        if not ckan_version:
            return None

        log.debug(
            f"Detected CKAN installation at {base_url} - found ckan_version={ckan_version} in {status_api_endpoint}"
        )

        return MaybeExists(CKANDataset(base_url, dataset_id))

    async def resolve(
        self, question: URL, log: Logger
    ) -> (
        Exists[Git]
        | MaybeExists[DataverseURL]
        | MaybeExists[GitLabURL]
        | MaybeExists[CKANDataset]
        | None
    ):
        if question.scheme not in ("http", "https"):
            return None

        detectors = (self.is_dataverse, self.is_gitlab, self.is_git_repo, self.is_ckan)

        async with aiohttp.ClientSession() as session:
            for g in detectors:
                maybe_answer = await g(session, question, log)
                if maybe_answer is not None:
                    return maybe_answer

        return None
