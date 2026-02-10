import json
import subprocess
from pathlib import Path
from tempfile import NamedTemporaryFile

from repoproviders.resolvers.rclone import ImmutableGoogleDriveFolder

from ..utils import GCP_PUBLIC_SERVICE_ACCOUNT_KEY


class GoogleDriveFetcher:

    async def fetch(self, repo: ImmutableGoogleDriveFolder, output_dir: Path):
        # FIXME: We ask for an ImmutableGoogleDriveFolder, but we could just as well fetch
        # a *mutable* one here, because we don't check dirhash after. What do we do with that?
        # UNCLEAR.
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
