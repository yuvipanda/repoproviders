import pytest

from repoproviders.resolvers.base import DoesNotExist, Exists
from repoproviders.resolvers.rclone import (
    GoogleDriveFolder,
    GoogleDriveFolderResolver,
    ImmutableGoogleDriveFolder,
)


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        # Immutable directory
        (
            GoogleDriveFolder(id="1OBwu72mlrWymv8DLepOwPY-GWHPrgYN8"),
            Exists(
                ImmutableGoogleDriveFolder(
                    id="1OBwu72mlrWymv8DLepOwPY-GWHPrgYN8",
                    dir_hash="hHea2vn_tW34FEXigXp2Eurs3adDso6XYgdeRhzPWPo=",
                )
            ),
        ),
        # Empty but public directory
        (
            GoogleDriveFolder("1sokbMclA4UaiXPdBBGyThlBEGv961psp"),
            DoesNotExist(
                GoogleDriveFolder,
                "The Google Drive Folder either does not exist, is empty or is not public",
            ),
        ),
        # Invalid ID
        (
            GoogleDriveFolder(id="1OBwu72mlrWymv8DLepOwPY-GWHPr8"),
            DoesNotExist(
                GoogleDriveFolder,
                "NOTICE: Failed to lsjson: error in ListJSON: couldn't list directory: googleapi: Error 404: File not found: ., notFound",
            ),
        ),
        # Private unshared folder
        (
            GoogleDriveFolder(id="1lvm0Co_aYa0iC__5QLyeL2ptcCNFpsIL"),
            DoesNotExist(
                GoogleDriveFolder,
                "The Google Drive Folder either does not exist, is empty or is not public",
            ),
        ),
    ),
)
async def test_gist(url, expected, log):
    gh = GoogleDriveFolderResolver()
    assert await gh.resolve(url, log) == expected
