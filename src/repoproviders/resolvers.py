from dataclasses import dataclass
from yarl import URL
import aiohttp

@dataclass
class Git:
    repo: str
    ref: str

@dataclass
class NotFound:
    pass

@dataclass
class Doi:
    url: str

class GitHubResolver:
    def resolve(self, url: URL) -> Git | None:
        if url.host != 'github.com' and url.host != 'www.github.com':
            # TODO: Allow configuring for GitHub enterprise
            return None

        # Split the URL into parts, discarding empty parts to account for leading and trailing slashes
        parts = [p for p in url.path.split('/') if p.strip() != ""]
        if len(parts) == 2:
            # Handle <user|org>/<repo>
            # Reconstruct the URL so we normalize any
            return Git(repo=str(url.with_path(f"{parts[0]}/{parts[1]}")), ref="HEAD")
        elif len(parts) >=4 and parts[2] in ("tree", "blob"):
            # Handle <user|org>/<repo>/<tree|blob>/<ref>(/<possible-path>)
            # Note: We ignore any paths specified here, as we only care about the repo
            return Git(repo=str(url.with_path(f"{parts[0]}/{parts[1]}")), ref=parts[3])
        else:
            # This is not actually a valid GitHub URL we support
            return None


class DoiResolver:
    """
    A *handle* resolver, called a Doi resolver because that's the most common handle
    """

    async def resolve(self, url: URL):
        # Check if this is a valid doi or handle
        if url.scheme in ("doi", "hdl"):
            doi = url.path
        elif url.scheme in ("http", "https") and url.host in ("doi.org", "www.doi.org", "hdl.handle.net"):
            doi = url.path.lstrip("/")
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


def resolve(question: str, recursive: bool):
    pass