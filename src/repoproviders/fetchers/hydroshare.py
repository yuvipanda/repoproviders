from logging import Logger
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

import aiohttp
from yarl import URL

from ..resolvers.repos import HydroshareDataset
from ..utils import download_file


class HydroshareFetcher:
    async def fetch(self, repo: HydroshareDataset, output_dir: Path, log: Logger):
        # This sometimes takes a while, as the zip file is dynamically generated on first GET
        # However, aiohttp seems to handle this behavior just fine no problem
        download_url = (
            URL("https://www.hydroshare.org/django_irods/download/bags/")
            / repo.resource_id
        )

        async with aiohttp.ClientSession() as session:
            with NamedTemporaryFile() as temp_file:
                await download_file(session, download_url, Path(temp_file.name))
                compressed_file = ZipFile(temp_file.name)
                # We want to only extract files from the data/contents
                contents_path = f"{repo.resource_id}/data/contents/"
                for file_info in compressed_file.infolist():
                    if file_info.filename.startswith(contents_path):
                        target_file_name = file_info.filename[len(contents_path) :]
                        file_info.filename = target_file_name
                        compressed_file.extract(file_info, output_dir)
