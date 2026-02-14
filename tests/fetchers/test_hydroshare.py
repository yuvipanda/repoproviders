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
            ("https://www.hydroshare.org/resource/e42d440acb0b438793b3cdf3bcc09315/",),
            {
                "kf-plantsoiln-alldata.csv": "02c8c5ce2d4673a5fcfbc9e2252bcd2c",
                "kf-soil-n-methods.pdf": "1ba86c4b05b54afe245ec7d9de68e154",
                "kf-variablesreported.csv": "ca96c95e9e4e413ced09005d0ccbaf94",
                "kf-resinn-alldata.csv": "858d2c52ae5f8f0a8920b400217fd8dc",
                "kf-four-plots.gpx.txt": "b9a3e2cde40fb5b7cbf550cb502ff99f",
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
