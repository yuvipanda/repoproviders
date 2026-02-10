import json
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

from repoproviders.resolvers.rclone import GoogleDriveFolder

from ..utils import GCP_PUBLIC_SERVICE_ACCOUNT_KEY


class GoogleDriveFetcher:

    async def fetch(self, repo: GoogleDriveFolder, output_dir: Path):
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
