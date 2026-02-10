import json
from dataclasses import dataclass
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
                # Failure in one way or another. Let's just write out the failure message
                # FIXME: Does this leak sensitive info?
                # Cut off first 20 chars, as it prints out the date
                return DoesNotExist(GoogleDriveFolder, stderr[20:].strip())

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
                if "Hashes" in item:
                    if "sha256" in item["Hashes"]:
                        hash_input[item["Path"]] = item["Hashes"]["sha256"]
                    else:
                        # Some old directories won't have sha256 but will have sha1
                        hash_input[item["Path"]] = item["Hashes"]["sha1"]
                else:
                    # Directories won't have hashes, so let's use Modified Time
                    hash_input[item["Path"]] = item["ModTime"]

            dirhash = make_dir_hash(hash_input)

            return Exists(ImmutableGoogleDriveFolder(question.id, dirhash))
