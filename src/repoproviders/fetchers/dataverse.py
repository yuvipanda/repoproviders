import os
from pathlib import Path

import aiohttp

from ..resolvers.doi import DataverseDataset
from ..utils import download_file


class DataverseFetcher:
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

                await download_file(session, file_download_url, output_dir / file_path)
