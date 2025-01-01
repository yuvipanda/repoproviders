import os
from pathlib import Path

import aiohttp
from yarl import URL

from ..resolvers.doi import DataverseDataset


class DataverseFetcher:
    async def download_file(
        self, session: aiohttp.ClientSession, url: URL, output_path: Path
    ):
        # Read in 4k chunks
        CHUNK_SIZE = 4 * 1024
        resp = await session.get(url)

        resp.raise_for_status()

        if not output_path.parent.exists():
            # Leave the exist_ok=True here despite the check, to handle possible
            # race conditions in the future if we ever parallelize this
            output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "wb") as f:
            async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
                f.write(chunk)

    async def fetch(self, repo: DataverseDataset, output_dir: Path):
        files_url = repo.installationUrl / "api/datasets/:persistentId"
        files_url = files_url.with_query(persistentId=repo.persistentId)

        async with aiohttp.ClientSession() as session:
            resp = await session.get(files_url)

            # FIXME: Do we assume this persistent_id has been *verified* to exist?
            # What kind of guarantee can our resolver actually give us? hmm
            resp.raise_for_status()

            files = (await resp.json())["data"]["latestVersion"]["files"]

            for f in files:
                file_download_url = (
                    repo.installationUrl / f"api/access/datafile/{f['dataFile']['id']}"
                )
                file_download_url = file_download_url.with_query(format="original")

                file_name = f["dataFile"].get("originalFileName", f["label"])

                file_path = Path(os.path.join(f.get("directoryLabel", ""), file_name))

                await self.download_file(
                    session, file_download_url, output_dir / file_path
                )
