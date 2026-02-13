import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

import aiohttp

from ..resolvers.doi import ImmutableFigshareDataset
from ..utils import download_file


class FigshareFetcher:
    async def fetch(self, repo: ImmutableFigshareDataset, output_dir: Path):
        # FIXME: Support other installation URLs
        api_url = (
            repo.installation.apiUrl
            / "articles"
            / str(repo.articleId)
            / "versions"
            / str(repo.version)
        )

        async with aiohttp.ClientSession() as session:
            resp = await session.get(api_url)

            # FIXME: Do we assume this persistent_id has been *verified* to exist?
            # What kind of guarantee can our resolver actually give us? hmm
            resp.raise_for_status()

            data = await resp.json()
            files = [f for f in data["files"] if not f["is_link_only"]]
            print(files)

            # Handle case when we only have one entry, and it's a zip file
            if len(files) == 1:
                # Only do this if mimetype is zip
                file = files[0]
                if file["mimetype"] == "application/zip":
                    download_url = file["download_url"]

                    with NamedTemporaryFile() as temp_file:
                        await download_file(session, download_url, Path(temp_file.name))
                        compressed_file = ZipFile(temp_file.name)
                        compressed_file.extractall(output_dir)

                        # If there's only one subdirectory, move its contents to the output directory
                        subdirs = list(output_dir.iterdir())
                        if len(subdirs) == 1:
                            # Just recursively move everything inside the subdir, rather than copy them
                            # This is safer (and probably faster) than using shutil.copytree
                            for d in subdirs[0].iterdir():
                                shutil.move(d, output_dir)
                            os.rmdir(subdirs[0])
                        # We're all done, no more processing to do
                        return

            # For cases with more than one entry, or if the one entry isn't a zip file
            for file in files:
                file_download_url = file["download_url"]

                # FIXME: Handle path traverseal attacks here?
                file_name = file["name"]

                # Zenodo doesn't support directory structures,
                # so we don't need to handle nesting https://support.zenodo.org/help/en-gb/1-upload-deposit/74-can-i-upload-folders-directories
                await download_file(session, file_download_url, output_dir / file_name)
