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
            (
                # Don't forget this happened
                "https://catalog.data.gov/dataset/cumulative-provisional-counts-of-deaths-by-sex-race-and-age",
            ),
            {
                "rows.rdf": "30c4b07b6fa28835db5daca0e2d6174e",
                "rows.csv": "48833a8e1e30ce06cc5a7562efa0b662",
                "rows.xml": "990d83bff832d6dd08e40037c97fca45",
                "rows.json": "5c76a18b6039ec5922e32b9bdc8bfde9",
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

            await fetch(answers[-1].repo, output_dir, log)

            # Verify md5 sum of the files we expect to find
            for subpath, expected_sha in md5tree.items():
                with open(output_dir / subpath, "rb") as f:
                    h = hashlib.md5()
                    h.update(f.read())
                    assert h.hexdigest() == expected_sha
