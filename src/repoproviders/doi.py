import json
import os
from dataclasses import dataclass

import aiohttp
from yarl import URL

from .resolvers import NotFound


@dataclass
class Doi:
    url: str


@dataclass
class DataverseDataset:
    installationUrl: str
    persistentId: str


class DoiResolver:
    """
    A *handle* resolver, called a Doi resolver because that's the most common handle
    """

    async def resolve(self, url: URL) -> Doi | NotFound | None:
        # Check if this is a valid doi or handle
        if url.scheme in ("doi", "hdl"):
            doi = url.path
        elif url.scheme in ("http", "https") and url.host in (
            "doi.org",
            "www.doi.org",
            "hdl.handle.net",
        ):
            doi = url.path.lstrip("/")
        elif url.scheme == "" and url.path.startswith("10."):
            # Handles in general are defined as <naming-authority>/<handle> (https://datatracker.ietf.org/doc/html/rfc3650#section-3)
            # however, this is far too broad, as even a file path like `hello/world` will satisfy it. Eventually, could find a list
            # of registered handle prefixes to validate the `<naming-authority>` part. In the meantime, we only check for a `10.` prefix,
            # which is for the most popular kind of handle - a DOI.
            # This is only for convenience - in cases when the user pastes in a DOI but doesn't actually say doi:.
            doi = url.path
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

    async def resolve(self, url: URL) -> DataverseDataset | NotFound | None:
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
            persistent_id = await self.get_dataset_id_from_file_id(
                installation, file_id
            )
            if persistent_id is None:
                return NotFound()

            # We know persistent_id is a dataset, because we asked the API!
            verified_dataset = True
        elif path.startswith("/file.xhtml"):
            file_persistent_id = qs["persistentId"]
            persistent_id = await self.get_dataset_id_from_file_id(
                installation, file_persistent_id
            )
            if persistent_id is None:
                return NotFound()
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
                persistent_id = await self.get_dataset_id_from_file_id(
                    installation, persistent_id
                )
                if persistent_id is None:
                    # This is not a file either, so this citation doesn't exist
                    return NotFound()
            else:
                # Any other errors should propagate
                resp.raise_for_status()

        # If we are here, it means the persistent_id is a dataset id, and we don't need to do anything else!
        return DataverseDataset(str(installation), persistent_id)
