import os
import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

import aiohttp
from yarl import URL

from ..resolvers.doi import ZenodoDataset
from ..utils import download_file


class ZenodoFetcher:
    async def fetch(self, repo: ZenodoDataset, output_dir: Path):
        files_url = repo.installationUrl / "api/records" / repo.recordId / "files"

        async with aiohttp.ClientSession() as session:
            resp = await session.get(files_url)

            # FIXME: Do we assume this persistent_id has been *verified* to exist?
            # What kind of guarantee can our resolver actually give us? hmm
            resp.raise_for_status()

            data = await resp.json()
            print(data)

            # Handle case when we only have one entry, and it's a zip file
            if len(data["entries"]) == 1:
                # Only do this if mimetype is zip
                entry = data["entries"][0]
                if entry["mimetype"] == "application/zip":
                    download_api_url = entry["links"]["content"]

                    download_url_resp = await session.get(download_api_url)
                    download_url = URL(await download_url_resp.text())

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
                        return

            # ALl other cases
            for entry in data["entries"]:
                file_download_url = entry["links"]["content"]

                file_name = entry["key"]

                file_path = file_name

                # FIXME: Does this handle directories?
                await download_file(session, file_download_url, output_dir / file_path)
