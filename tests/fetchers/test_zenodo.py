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
            # Test fetching a record with a single zip file that we then extract,
            # Also accounting for data.caltech.edu sending back 200 response with Location headers
            ("https://data.caltech.edu/records/996aw-mf266",),
            {
                "CaltechDATA_Usage_Graphs.ipynb": "3bb3a97b879112b1ab70923636d63e87",
                "LICENSE": "be9d12a5904d8e4ef6df52c86d2db34a",
                "requirements.txt": "b0081730d38ec5f28f3fea4f843816ce",
                "README.md": "59a0e5157faef752532fe51a2d490c9c",
                ".gitignore": "2a9ac83919f923cc25ea380b19a2a7d9",
                "codemeta.json": "8aa017724932fbdff3d2240c932487b7",
            },
        ),
        (
            # Test fetching a record with a single zip file, without the 200 / Location header
            # issue
            ("https://sandbox.zenodo.org/records/432153",),
            {
                "LICENSE": "65d3616852dbf7b1a6d4b53b00626032",
                "README.md": "041917c62158f2dec74eb1ead07662f1",
                "rutgers.txt": "2f501f69915cbcf0fb185f9e8bdb1c96",
            },
        ),
        (
            # Test fetching a record with a single file that is *not* a zip file
            ("https://sandbox.zenodo.org/records/415845",),
            {"136_poster_-_Dalia_Al-Shahrabi.pdf": "663a007fead7da7f9f6f7ddae71db254"},
        ),
        (
            # Test fetching multiple files without a zip file
            ("https://sandbox.zenodo.org/records/98954",),
            {
                "sampleFile.json": "9c9cf2a3740a65cc3268e12567eed67b",
                "sampleFile.txt": "fedb53c2017c1aad5bf9293b7ce03a71",
            },
        ),
    ],
)
async def test_fetch(questions: list[str], md5tree: dict[str, str], log: Logger):
    for question in questions:
        with TemporaryDirectory() as d:
            output_dir = Path(d)
            answers = await resolve(question, True, log)

            assert answers is not None
            assert not isinstance(answers[-1], DoesNotExist)

            await fetch(answers[-1].repo, output_dir, log)

            # Verify md5 sum of the files we expect to find
            for subpath, expected_sha in md5tree.items():
                with open(output_dir / subpath, "rb") as f:
                    h = hashlib.md5()
                    h.update(f.read())
                    assert h.hexdigest() == expected_sha
