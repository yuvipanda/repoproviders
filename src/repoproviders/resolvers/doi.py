import json
import os
from dataclasses import dataclass

import aiohttp
from yarl import URL

from .base import NotFound


@dataclass(frozen=True)
class Doi:
    url: str

    # This needs further investigation
    immutable = False


@dataclass(frozen=True)
class DataverseDataset:
    installationUrl: URL
    persistentId: str

    # Dataverse Datasets also have versions, which are not represented here.
    immutable = False


@dataclass(frozen=True)
class ZenodoDataset:
    installationUrl: URL
    recordId: str

    # Zenodo records are immutable: https://help.zenodo.org/docs/deposit/about-records/#life-cycle
    # When a new version is published, it gets its own record id!
    immutable = True


@dataclass(frozen=True)
class FigshareInstallation:
    url: URL
    apiUrl: URL


@dataclass(frozen=True)
class FigshareDataset:
    installation: FigshareInstallation
    articleId: int
    version: int | None

    # Figshare articles have versions, and here we don't know if this one does or not
    immutable = False


@dataclass(frozen=True)
class ImmutableFigshareDataset:
    installation: FigshareInstallation
    articleId: int
    # version will always be present when immutable
    version: int

    # We *know* there's a version here
    immutable = True


class DoiResolver:
    """
    A *handle* resolver, called a Doi resolver because that's the most common handle
    """

    async def resolve(self, question: URL) -> Doi | NotFound | None:
        # Check if this is a valid doi or handle
        if question.scheme in ("doi", "hdl"):
            doi = question.path
        elif question.scheme in ("http", "https") and question.host in (
            "doi.org",
            "www.doi.org",
            "hdl.handle.net",
        ):
            doi = question.path.lstrip("/")
        elif question.scheme == "" and question.path.startswith("10."):
            # Handles in general are defined as <naming-authority>/<handle> (https://datatracker.ietf.org/doc/html/rfc3650#section-3)
            # however, this is far too broad, as even a file path like `hello/world` will satisfy it. Eventually, could find a list
            # of registered handle prefixes to validate the `<naming-authority>` part. In the meantime, we only check for a `10.` prefix,
            # which is for the most popular kind of handle - a DOI.
            # This is only for convenience - in cases when the user pastes in a DOI but doesn't actually say doi:.
            doi = question.path
        else:
            # Not a DOI or handle
            return None

        # TODO: Make the handle resolver we use configurable
        api_url = f"https://doi.org/api/handles/{doi}"

        # FIXME: Reuse this
        async with aiohttp.ClientSession() as session:
            resp = await session.get(api_url)

            if resp.status == 404:
                # This is a validly *formatted* DOI, but it's not actually a dOI
                return NotFound()
            elif resp.status == 200:
                data = await resp.json()

                # Pick the first URL we find from the doi response
                for v in data["values"]:
                    if v["type"] == "URL":
                        return Doi(v["data"]["value"])

                # No URLs found for this DOI, so we treat it as NotFound
                return NotFound()
            else:
                # Some other kind of failure, let's propagate our error up
                resp.raise_for_status()
                # This should not actually be reached, but the explicit return None makes mypy happy
                return None


class DataverseResolver:
    def __init__(self):
        # Get a list of installation URLs for known dataverse installations
        data_file = os.path.join(os.path.dirname(__file__), "dataverse.json")
        with open(data_file) as fp:
            installations = json.load(fp)["installations"]

        # Parse all the URLs of installations once, so we can quickly use them for validating URLs passed in
        # TODO: Use a better datastructure here (like a trie?)
        self.installation_urls = [URL(i["url"]) for i in installations]

        super().__init__()

    async def get_dataset_id_from_file_id(
        self, installation_url: URL, file_id: str
    ) -> str | None:
        """
        Return the persistent_id (DOI) of a dataset that a given file_id (int or doi) belongs to
        """
        if file_id.isdigit():
            # the file_id is an integer, rather than a persistent id (DOI)
            api_url = installation_url / "api/files" / file_id
            api_url = api_url.with_query(returnDatasetVersion="true")
        else:
            # the file_id is a doi itself
            api_url = installation_url / "api/files/:persistentId"
            api_url = api_url.with_query(
                returnDatasetVersion="true", persistentId=file_id
            )

        async with aiohttp.ClientSession() as session:
            resp = await session.get(api_url)

        if resp.status == 404:
            return None
        else:
            resp.raise_for_status()

        data = (await resp.json())["data"]
        return data["datasetVersion"]["datasetPersistentId"]

    async def resolve(self, question: URL | Doi) -> DataverseDataset | NotFound | None:
        if isinstance(question, URL):
            url = question
        elif isinstance(question, Doi):
            url = URL(question.url)
        # Check if URL is under one of the installation URLs we have.
        installation = next(
            (
                installation
                for installation in self.installation_urls
                # Intentionally don't check for scheme validity, to support interchangeable http and https URLs
                if installation.host == url.host
                and url.path.startswith(installation.path)
            ),
            None,
        )
        if installation is None:
            return None
        path = url.path
        qs = url.query

        # https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/DVN/TJCLKP
        if path.startswith("/citation"):
            persistent_id = qs["persistentId"]
            # We don't know if this is a dataset or file id yet
            verified_dataset = False
        # https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/TJCLKP
        elif path.startswith("/dataset.xhtml"):
            #  https://dataverse.harvard.edu/api/access/datafile/3323458
            persistent_id = qs["persistentId"]
            # We haven't verified this dataset exists
            verified_dataset = False
        elif path.startswith("/api/access/datafile"):
            # What we have here is an entity id, which we can use to get a persistentId
            file_id = os.path.basename(path)
            pid_maybe = await self.get_dataset_id_from_file_id(installation, file_id)
            if pid_maybe is None:
                return NotFound()
            else:
                persistent_id = pid_maybe

            # We know persistent_id is a dataset, because we asked the API!
            verified_dataset = True
        elif path.startswith("/file.xhtml"):
            file_persistent_id = qs["persistentId"]
            pid_maybe = await self.get_dataset_id_from_file_id(
                installation, file_persistent_id
            )
            if pid_maybe is None:
                return NotFound()
            else:
                persistent_id = pid_maybe
            # We know persistent_id is a dataset, because we asked the API!
            verified_dataset = True
        else:
            return NotFound()

        if not verified_dataset:
            # citations can be either datasets or files - we don't know. The most common case is that it is
            # a dataset, so we check if it is first.
            api_url = installation / "api/datasets/:persistentId"
            api_url = api_url.with_query(persistentId=persistent_id)
            async with aiohttp.ClientSession() as session:
                resp = await session.get(api_url)

            if resp.status == 404:
                # This persistent id is *not* a dataset. Maybe it's a file?
                pid_maybe = await self.get_dataset_id_from_file_id(
                    installation, persistent_id
                )
                if pid_maybe is None:
                    # This is not a file either, so this citation doesn't exist
                    return NotFound()
                else:
                    persistent_id = pid_maybe
            else:
                # Any other errors should propagate
                resp.raise_for_status()

        # If we are here, it means the persistent_id is a dataset id, and we don't need to do anything else!
        return DataverseDataset(installation, persistent_id)


class ZenodoResolver:
    """
    A resolver for datasets hosted on https://inveniosoftware.org/ (such as Zenodo)
    """

    def __init__(self):
        # FIXME: Determine this dynamically in the future
        self.installations = [
            URL("https://sandbox.zenodo.org/"),
            URL("https://zenodo.org/"),
            URL("https://data.caltech.edu/"),
        ]

    async def resolve(self, question: URL | Doi) -> ZenodoDataset | NotFound | None:
        if isinstance(question, URL):
            url = question
        elif isinstance(question, Doi):
            url = URL(question.url)

        installation = next(
            (
                installation
                for installation in self.installations
                # Intentionally don't check for scheme validity, to support interchangeable http and https URLs
                if installation.host == url.host
                # Check for base URL, to support installations on base URL other than /
                and url.path.startswith(installation.path)
                and (
                    # After the base URL, the URL structure should start with either record or records
                    url.path[len(installation.path) :].startswith("record/")
                    or url.path[len(installation.path) :].startswith("records/")
                    or url.path[len(installation.path) :].startswith("doi/")
                )
            ),
            None,
        )
        if installation is None:
            return None

        # For URLs of form https://zenodo.org/doi/<doi>, the record_id can be resolved by making a
        # HEAD request and following it. This is absolutely *unideal* - you would really instead want
        # to make an API call. But I can't seem to find anything in the REST API that would let me give
        # it a DOI and return a record_id. And these dois can resolve to *different* records over time,
        # so let's actively resolve them here to match the ZenodoDataset's immutable property
        if url.path[len(installation.path) :].startswith("doi/"):
            url_parts = url.path.split("/")
            if len(url_parts) != 4:
                # Not a correctly formatted DOI
                return NotFound()

            async with aiohttp.ClientSession() as session:
                resp = await session.head(url)

            if resp.status == 404:
                return NotFound()
            redirect_location = resp.headers["Location"]

            return await self.resolve(URL(redirect_location))
        else:
            # URL is /record or /records
            # Record ID is the last part of the URL path
            return ZenodoDataset(installation, url.name)


class FigshareResolver:
    def __init__(self):
        # FIXME: Determine this dynamically in the future
        # Figshare can be on custom domains: https://figshare.com/blog/Figshare_now_available_on_custom_domains/461
        self.installations = [
            FigshareInstallation(
                URL("https://figshare.com/"), URL("https://api.figshare.com/v2/")
            )
        ]

    async def resolve(self, question: URL | Doi) -> FigshareDataset | None:
        if isinstance(question, URL):
            url = question
        elif isinstance(question, Doi):
            url = URL(question.url)

        installation = next(
            (
                installation
                for installation in self.installations
                # Intentionally don't check for scheme validity, to support interchangeable http and https URLs
                if installation.url.host == url.host
                # Check for base URL, to support installations on base URL other than /
                and url.path.startswith(installation.url.path)
                and (
                    # After the base URL, the URL structure should start with either record or records
                    url.path[len(installation.url.path) :].startswith("articles/")
                    or url.path[len(installation.url.path) :].startswith(
                        "account/articles/"
                    )
                )
            ),
            None,
        )
        if installation is None:
            return None

        # Figshare article IDs are integers, and so are version IDs
        # If last two segments of the URL are integers, treat them as article ID and version ID
        # If not, treat it as article ID only
        parts = url.path.split("/")
        if parts[-1].isdigit() and parts[-2].isdigit():
            return FigshareDataset(installation, int(parts[-2]), int(parts[-1]))
        elif parts[-1].isdigit():
            return FigshareDataset(installation, int(parts[-1]), None)
        else:
            return None


class ImmutableFigshareResolver:
    async def resolve(
        self, question: FigshareDataset
    ) -> ImmutableFigshareDataset | NotFound | None:
        if question.version is not None:
            # Version already specified, just return
            return ImmutableFigshareDataset(
                question.installation, question.articleId, question.version
            )

        api_url = (
            question.installation.apiUrl
            / "articles"
            / str(question.articleId)
            / "versions"
        )

        async with aiohttp.ClientSession() as session:
            resp = await session.get(api_url)

        if resp.status == 404:
            return NotFound()
        elif resp.status == 200:
            data = await resp.json()
            return ImmutableFigshareDataset(
                question.installation, question.articleId, data[-1]["version"]
            )
        else:
            # All other status codes should raise an error
            resp.raise_for_status()
            # This should not actually be reached, but the explicit return None makes mypy happy
            return None
