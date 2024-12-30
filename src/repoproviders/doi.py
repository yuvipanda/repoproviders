from dataclasses import dataclass
from yarl import URL
import aiohttp
from .resolvers import NotFound

@dataclass
class Doi:
    url: str

class DoiResolver:
    """
    A *handle* resolver, called a Doi resolver because that's the most common handle
    """

    async def resolve(self, url: URL) -> Doi | NotFound | None:
        # Check if this is a valid doi or handle
        if url.scheme in ("doi", "hdl"):
            doi = url.path
        elif url.scheme in ("http", "https") and url.host in ("doi.org", "www.doi.org", "hdl.handle.net"):
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


