import asyncio
import json
from dataclasses import dataclass
from tempfile import NamedTemporaryFile

from repoproviders.resolvers.base import DoesNotExist, Exists

from ..utils import GCP_PUBLIC_SERVICE_ACCOUNT_KEY, make_dir_hash


@dataclass(frozen=True)
class GoogleDriveItem:
    id: str

    immutable = False


@dataclass(frozen=True)
class ImmutableGoogleDriveItem:
    id: str
    dir_hash: str

    immutable = True


class GoogleDriveItemResolver:
    async def resolve(
        self, question: GoogleDriveItem
    ) -> Exists[ImmutableGoogleDriveItem] | DoesNotExist[GoogleDriveItem] | None:

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

            proc = await asyncio.create_subprocess_exec(
                *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            await proc.wait()

            if proc.returncode != 0:
                # Failure in one way or another. Let's just write out the failure message
                # FIXME: Does this leak sensitive info?
                return DoesNotExist(GoogleDriveItem, stderr.decode().strip())

            data = json.loads(stdout.decode())
            print(data)

            if len(data) == 0:
                # No items were returned. Let's treat this as a DoesNotExist, as this usually means we don't
                # have permissions, or the directory doesn't exist
                return DoesNotExist(
                    GoogleDriveItem,
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

            return Exists(ImmutableGoogleDriveItem(question.id, dirhash))
