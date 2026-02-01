from pathlib import Path

import aiohttp
from yarl import URL


async def download_file(session: aiohttp.ClientSession, url: URL, output_path: Path):
    # Read in 4k chunks
    CHUNK_SIZE = 4 * 1024
    resp = await session.get(url)

    if resp.status == 200 and "Location" in resp.headers:
        # Some providers (lookin at you, data.caltech.edu) send a Location header
        # *but with a 200 status code*. This is invalid and bogus, yet we have to
        # honor it. Sigh
        return await download_file(session, URL(resp.headers["Location"]), output_path)

    resp.raise_for_status()

    if not output_path.parent.exists():
        # Leave the exist_ok=True here despite the check, to handle possible
        # race conditions in the future if we ever parallelize this
        output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
            f.write(chunk)
