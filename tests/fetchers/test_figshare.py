import hashlib
from logging import Logger
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from repoproviders.fetchers import fetch
from repoproviders.resolvers import resolve
from repoproviders.resolvers.base import DoesNotExist


@pytest.mark.parametrize(
    ("questions", "md5tree"),
    [
        (
            ("https://figshare.com/account/articles/31337494",),
            {
                "tests/test_utils.py": "8cc64b23ca72e6c2d2b8116a69a8764b",
                "tests/fetchers/test_google_drive.py": "26dde4ac8621070939cd5840ed3cf364",
                "tests/fetchers/test_github_actions_artifacts.py": "23d2577046eb52302466195b939ed72a",
                "tests/fetchers/test_zenodo.py": "83c16eedb777a1fe62b58f7b50e82105",
                "tests/fetchers/test_dataverse.py": "dcda177e04c9b36aa4c519dc2de5bd58",
                "tests/resolvers/test_google_drive.py": "bdb50593d6bc21036b9b744db4e9ae85",
                "tests/resolvers/test_resolve.py": "961ab5fb4fb9d8fbc81f9c5fc567ca2d",
                "tests/resolvers/test_figshare.py": "ad7c199437ef098904605466c1ab0fbb",
                "tests/resolvers/test_github.py": "f0e753e032a682504bd14b0fce4aef36",
                "tests/resolvers/test_wellknown.py": "9bc1d525dabefd123a34cb35c8e8f688",
                "tests/resolvers/test_feature_detect.py": "ce8cd6f5bb5378e4a283cedfad8ad341",
                "tests/resolvers/test_gist.py": "12e4f33eb78dca763d4940889e1fcc93",
                "tests/resolvers/test_doi.py": "5d7981b1f9f854557eaaefb90e8a7082",
                "tests/resolvers/test_giturl.py": "4080c8d6c3f0c015852340139ddc3636",
                "tests/resolvers/test_serialize.py": "b8c52284b9ede5b4adaed5416341002e",
                "tests/resolvers/test_zenodo.py": "78c6626331808a502d1115f1a0eac40c",
                "tests/resolvers/test_gitlab.py": "8570dc96679c953e5070132359965505",
                "tests/resolvers/test_immutablegit.py": "a37b556bca603e2fed5f06e41ecceef2",
                "tests/resolvers/test_dataverse.py": "119292866587531f2e3a3d0523491fd4",
            },
        )
    ],
)
async def test_fetch(questions: list[str], md5tree: dict[str, str], log: Logger):
    for question in questions:
        with TemporaryDirectory() as d:
            output_dir = Path(d)
            answers = await resolve(question, True, log)

            assert answers is not None
            assert not isinstance(answers[-1], DoesNotExist)

            await fetch(answers[-1].repo, output_dir)

            # Verify md5 sum of the files we expect to find
            for subpath, expected_sha in md5tree.items():
                with open(output_dir / subpath, "rb") as f:
                    h = hashlib.md5()
                    h.update(f.read())
                    assert h.hexdigest() == expected_sha
