import os

import aiohttp
from yarl import URL

from .base import DoesNotExist, Exists, MaybeExists
from .urls import (
    DataverseDataset,
    DataverseURL,
    Doi,
    FigshareDataset,
    FigshareURL,
    ImmutableFigshareDataset,
    ZenodoDataset,
    ZenodoURL,
)


class DoiResolver:
    """
    A *handle* resolver, called a Doi resolver because that's the most common handle
    """

    async def resolve(self, question: URL) -> Exists[Doi] | DoesNotExist[Doi] | None:
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
                return DoesNotExist(Doi, f"{doi} is not a registered DOI or handle")
            elif resp.status == 200:
                data = await resp.json()

                # Pick the first URL we find from the doi response
                for v in data["values"]:
                    if v["type"] == "URL":
                        return Exists(Doi(URL(v["data"]["value"])))

                # No URLs found for this DOI, so we treat it as DoesNotExist
                return DoesNotExist(Doi, f"{doi} does not point to any URL")
            else:
                # Some other kind of failure, let's propagate our error up
                resp.raise_for_status()
                # This should not actually be reached, but the explicit return None makes mypy happy
                return None


class DataverseResolver:
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

    async def resolve(
        self, question: DataverseURL
    ) -> Exists[DataverseDataset] | DoesNotExist[DataverseDataset] | None:
        url = question.url
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
            pid_maybe = await self.get_dataset_id_from_file_id(
                question.installation, file_id
            )
            if pid_maybe is None:
                return DoesNotExist(
                    DataverseDataset,
                    f"No file with id {file_id} found in dataverse installation {question.installation}",
                )
            else:
                persistent_id = pid_maybe

            # We know persistent_id is a dataset, because we asked the API!
            verified_dataset = True
        elif path.startswith("/file.xhtml"):
            file_id = qs["persistentId"]
            pid_maybe = await self.get_dataset_id_from_file_id(
                question.installation, file_id
            )
            if pid_maybe is None:
                return DoesNotExist(
                    DataverseDataset,
                    f"No file with id {file_id} found in dataverse installation {question.installation}",
                )
            else:
                persistent_id = pid_maybe
            # We know persistent_id is a dataset, because we asked the API!
            verified_dataset = True
        else:
            # This URL is not actually a dataverse dataset URL
            return None

        if not verified_dataset:
            # citations can be either datasets or files - we don't know. The most common case is that it is
            # a dataset, so we check if it is first.
            api_url = question.installation / "api/datasets/:persistentId"
            api_url = api_url.with_query(persistentId=persistent_id)
            async with aiohttp.ClientSession() as session:
                resp = await session.get(api_url)

            if resp.status == 404:
                # This persistent id is *not* a dataset. Maybe it's a file?
                pid_maybe = await self.get_dataset_id_from_file_id(
                    question.installation, persistent_id
                )
                if pid_maybe is None:
                    # This is not a file either, so this citation doesn't exist
                    return DoesNotExist(
                        DataverseDataset,
                        f"{persistent_id} is neither a file nor a dataset in {question.installation}",
                    )
                else:
                    persistent_id = pid_maybe
            elif resp.status == 200:
                # This *is* a dataset, we just verified it with this query
                verified_dataset = True
            else:
                # Any other errors should propagate
                resp.raise_for_status()

                return None

        return Exists(DataverseDataset(question.installation, persistent_id))


class ZenodoResolver:
    """
    A resolver for datasets hosted on https://inveniosoftware.org/ (such as Zenodo)
    """

    async def resolve(
        self, question: ZenodoURL
    ) -> MaybeExists[ZenodoDataset] | DoesNotExist[ZenodoDataset] | None:
        if not (
            # After the base URL, the URL structure should start with either record or records
            question.url.path[len(question.installation.path) :].startswith("record/")
            or question.url.path[len(question.installation.path) :].startswith(
                "records/"
            )
            or question.url.path[len(question.installation.path) :].startswith("doi/")
        ):
            return None
        # For URLs of form https://zenodo.org/doi/<doi>, the record_id can be resolved by making a
        # HEAD request and following it. This is absolutely *unideal* - you would really instead want
        # to make an API call. But I can't seem to find anything in the REST API that would let me give
        # it a DOI and return a record_id. And these dois can resolve to *different* records over time,
        # so let's actively resolve them here to match the ZenodoDataset's immutable property
        if question.url.path[len(question.installation.path) :].startswith("doi/"):
            url_parts = question.url.path.split("/")
            if len(url_parts) != 4:
                # Not a correctly formatted DOI URL
                return None

            async with aiohttp.ClientSession() as session:
                resp = await session.head(question.url)

            if resp.status == 404:
                return DoesNotExist(
                    ZenodoDataset, f"{question.url} is not a valid Zenodo DOI URL"
                )
            redirect_location = resp.headers["Location"]

            return await self.resolve(
                ZenodoURL(question.installation, URL(redirect_location))
            )
        else:
            # URL is /record or /records
            # Record ID is the last part of the URL path
            return MaybeExists(ZenodoDataset(question.installation, question.url.name))


class FigshareResolver:
    async def resolve(
        self, question: FigshareURL
    ) -> MaybeExists[FigshareDataset] | None:
        # After the base URL, the URL structure should start with either articles or account/articles
        if not (
            question.url.path[len(question.installation.url.path) :].startswith(
                "articles/"
            )
            or question.url.path[len(question.installation.url.path) :].startswith(
                "account/articles/"
            )
        ):
            return None
        # Figshare article IDs are integers, and so are version IDs
        # If last two segments of the URL are integers, treat them as article ID and version ID
        # If not, treat it as article ID only
        parts = question.url.path.split("/")
        if parts[-1].isdigit() and parts[-2].isdigit():
            return MaybeExists(
                FigshareDataset(question.installation, int(parts[-2]), int(parts[-1]))
            )
        elif parts[-1].isdigit():
            return MaybeExists(
                FigshareDataset(question.installation, int(parts[-1]), None)
            )
        else:
            return None


class ImmutableFigshareResolver:
    async def resolve(
        self, question: FigshareDataset
    ) -> (
        Exists[ImmutableFigshareDataset]
        | MaybeExists[ImmutableFigshareDataset]
        | DoesNotExist[ImmutableFigshareDataset]
        | None
    ):
        if question.version is not None:
            # Version already specified, just return
            return MaybeExists(
                ImmutableFigshareDataset(
                    question.installation, question.articleId, question.version
                )
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
            return DoesNotExist(
                ImmutableFigshareDataset,
                f"Article ID {question.articleId} not found on figshare installation {question.installation.url}",
            )
        elif resp.status == 200:
            data = await resp.json()
            return Exists(
                ImmutableFigshareDataset(
                    question.installation, question.articleId, data[-1]["version"]
                )
            )
        else:
            # All other status codes should raise an error
            resp.raise_for_status()
            # This should not actually be reached, but the explicit return None makes mypy happy
            return None
