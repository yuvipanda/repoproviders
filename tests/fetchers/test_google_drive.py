import hashlib
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
            # Fetch an immutable subdir set up in yuvipanda's drive and is public
            # We pick a small but still nested dir to make the test faster
            (
                "https://drive.google.com/drive/folders/12zoh_LubWyRMZG-KR9GGyukBsO8SCU9j",
            ),
            {
                "PULL_REQUEST_TEMPLATE.md": "0dc1f0612f21713189ed4ccc0d00197b",
                "SUPPORT.md": "14ddad47a068e1660d37fcef01026763",
                "workflows/release.yml": "0646032f1588e8b8621cd1c153bb6fbf",
                "workflows/test.yml": "d778015caa14985a6f61757de44bd5e0",
                "workflows/cron.yml": "3d055970af426e2065403d11dfa526b6",
                "workflows/main.yml": "70271a5c0e3dab1a25df2f6b3f8449eb",
                "ISSUE_TEMPLATE/02-question.yml": "7d7fceedd5b01853f575e0dff757f536",
                "ISSUE_TEMPLATE/03-feature-request.yml": "a1d4f142c8503aa7220220877416106a",
                "ISSUE_TEMPLATE/config.yml": "0311551ec2b71e6f8892ba688ea57dd7",
                "ISSUE_TEMPLATE/01-bug-report.yml": "c23bc48db00e2a5f48185f395614fbf7",
            },
        ),
    ],
)
async def test_fetch(questions: list[str], md5tree: dict[str, str]):
    for question in questions:
        with TemporaryDirectory() as d:
            output_dir = Path(d)
            answers = await resolve(question, True)

            assert answers is not None
            assert not isinstance(answers[-1], DoesNotExist)

            await fetch(answers[-1].repo, output_dir)

            # Verify md5 sum of the files we expect to find
            for subpath, expected_sha in md5tree.items():
                with open(output_dir / subpath, "rb") as f:
                    h = hashlib.md5()
                    h.update(f.read())
                    assert h.hexdigest() == expected_sha
