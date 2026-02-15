import os
import shutil
from logging import Logger
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

import aiohttp

from ..resolvers.doi import ZenodoDataset
from ..utils import download_file


class ZenodoFetcher:
    async def fetch(self, repo: ZenodoDataset, output_dir: Path, log: Logger):
        files_url = repo.installationUrl / "api/records" / repo.recordId / "files"

        async with aiohttp.ClientSession() as session:
            resp = await session.get(files_url)

            # FIXME: Do we assume this persistent_id has been *verified* to exist?
            # What kind of guarantee can our resolver actually give us? hmm
            resp.raise_for_status()

            data = await resp.json()

            # Handle case when we only have one entry, and it's a zip file
            if len(data["entries"]) == 1:
                # Only do this if mimetype is zip
                entry = data["entries"][0]
                if entry["mimetype"] == "application/zip":
                    download_url = entry["links"]["content"]

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
            for entry in data["entries"]:
                file_download_url = entry["links"]["content"]

                # FIXME: Handle path traverseal attacks here?
                file_name = entry["key"]

                # Zenodo doesn't support directory structures,
                # so we don't need to handle nesting https://support.zenodo.org/help/en-gb/1-upload-deposit/74-can-i-upload-folders-directories
                await download_file(session, file_download_url, output_dir / file_name)
