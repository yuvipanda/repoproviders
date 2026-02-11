import json
from dataclasses import dataclass
from shutil import which
from tempfile import NamedTemporaryFile

from repoproviders.resolvers.base import DoesNotExist, Exists

from ..utils import GCP_PUBLIC_SERVICE_ACCOUNT_KEY, exec_process, make_dir_hash


@dataclass(frozen=True)
class GoogleDriveFolder:
    id: str

    immutable = False


@dataclass(frozen=True)
class ImmutableGoogleDriveFolder:
    id: str
    dir_hash: str

    immutable = True


class GoogleDriveFolderResolver:
    async def resolve(
        self, question: GoogleDriveFolder
    ) -> Exists[ImmutableGoogleDriveFolder] | DoesNotExist[GoogleDriveFolder] | None:

        if not which("rclone"):
            raise FileNotFoundError(
                "rclone must be installed to resolve folders from Google Drive"
            )
        with NamedTemporaryFile("w") as service_account_key:
            json.dump(GCP_PUBLIC_SERVICE_ACCOUNT_KEY, service_account_key)
            service_account_key.flush()

            connection_string = f":drive,scope=drive.readonly,service_account_file={service_account_key.name}:"

            cmd = [
                "rclone",
                "lsjson",
                connection_string,
                "--recursive",
                "--hash",
                "--drive-root-folder-id",
                question.id,
            ]

            returncode, stdout, stderr = await exec_process(cmd)

            if returncode != 0:
                # Failure in one way or another. Let's just write out the failure message lines
                # that refer to lsjson, so we avoid messages about missing config files
                # Cut off first 20 chars, as it prints out the date
                stderr_lines = [l[20:] for l in stderr.splitlines()]
                message = " ".join(l for l in stderr_lines if "lsjson" in l)
                # FIXME: Does this leak sensitive info?
                return DoesNotExist(GoogleDriveFolder, message)

            data = json.loads(stdout)

            if len(data) == 0:
                # No items were returned. Let's treat this as a DoesNotExist, as this usually means we don't
                # have permissions, or the directory doesn't exist
                return DoesNotExist(
                    GoogleDriveFolder,
                    "The Google Drive Folder either does not exist, is empty or is not public",
                )

            hash_input = {}
            for item in data:
                # Use (in order of preference), sha256, sha1, md5 and modtime based on what is present
                hashes = item.get("Hashes")
                h = hashes.get(
                    "sha256", hashes.get("sha1", hashes.get("md5", item["ModTime"]))
                )
                hash_input[item["Path"]] = h

            dirhash = make_dir_hash(hash_input)

            return Exists(ImmutableGoogleDriveFolder(question.id, dirhash))
