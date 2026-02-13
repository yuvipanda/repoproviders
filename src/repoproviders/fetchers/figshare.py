from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

import aiohttp

from ..resolvers.doi import ImmutableFigshareDataset
from ..utils import download_file


class FigshareFetcher:
    async def fetch(self, repo: ImmutableFigshareDataset, output_dir: Path):
        download_url = (
            repo.installation.apiUrl
            / "articles"
            / str(repo.articleId)
            / "versions"
            / str(repo.version)
            / "download"
        )

        async with aiohttp.ClientSession() as session:
            with NamedTemporaryFile() as temp_file:
                await download_file(session, download_url, Path(temp_file.name))
                compressed_file = ZipFile(temp_file.name)
                compressed_file.extractall(output_dir)
