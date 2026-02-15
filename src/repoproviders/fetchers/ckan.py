from logging import Logger
from pathlib import Path

import aiohttp
from yarl import URL

from ..resolvers.repos import CKANDataset
from ..utils import download_file


class CKANFetcher:
    async def fetch(self, repo: CKANDataset, output_dir: Path, log: Logger):
        api_url = (repo.installationUrl / "api/3/action/package_show").with_query(
            id=repo.dataset_id
        )

        async with aiohttp.ClientSession() as session:
            resp = await session.get(api_url)

            # FIXME: Handle this is not found correctly
            resp.raise_for_status()
            data = await resp.json()

            resources = data["result"]["resources"]

            for r in resources:
                file_download_url = URL(r["url"])

                # There isn't a consistent naming situation for files. We try the last part of file url as filename
                parts = [s for s in file_download_url.path.split("/") if s]
                file_name = parts[-1]
                # FIXME: Do we support folder structures?
                file_path = file_name

                await download_file(
                    session, file_download_url, output_dir / file_path, log
                )
