import json
import subprocess
from pathlib import Path
from shutil import which
from tempfile import NamedTemporaryFile

from repoproviders.resolvers.rclone import GoogleDriveFolder, ImmutableGoogleDriveFolder

from ..utils import GCP_PUBLIC_SERVICE_ACCOUNT_KEY


class GoogleDriveFolderFetcher:
    async def fetch(
        self, repo: ImmutableGoogleDriveFolder | GoogleDriveFolder, output_dir: Path
    ):
        if not which("rclone"):
            raise FileNotFoundError(
                "rclone must be installed to fetch folders from Google Drive"
            )
        # FIXME: We don't actually check the dirhash of the ImmutableGoogleDriveFolder, so it may have
        # mutated since we asked for things to be done to it. I don't exactly know what to do about that.
        with NamedTemporaryFile("w") as service_account_key:
            json.dump(GCP_PUBLIC_SERVICE_ACCOUNT_KEY, service_account_key)
            service_account_key.flush()

            connection_string = f":drive,scope=drive.readonly,service_account_file={service_account_key.name}:"
            rclone_cmd = [
                "rclone",
                "copy",
                connection_string,
                "--drive-root-folder-id",
                repo.id,
                str(output_dir),
            ]

            subprocess.check_call(rclone_cmd)
