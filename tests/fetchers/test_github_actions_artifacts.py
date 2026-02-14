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
            # These expire after 90 days. We should set up our own github automation for this.
            # However, instead, I'll buy us 90 days by using a recent run.
            # We expect this to fail roughly 90 days from now.
            # When that happens, you can either:
            # 1. Fix this properly by rewriting the test here to dynamically look for artifacts
            # 2. Go to https://github.com/jupyterlab/jupyterlab/actions/workflows/galata.yml, pick a
            #    recent completed run, find the URL for `documentation-test-assets` and update the content
            # https://github.com/yuvipanda/repoproviders/issues/28 has more information
            (
                "https://github.com/jupyterlab/jupyterlab/actions/runs/21958742242/artifacts/5487665511",
            ),
            {
                "test-documentation-workspa-aae0b-bar-Workspaces-context-menu-documentation/video.webm": "e2f7acd5785ed28ec6177081e8a7f7e8",
                "test-documentation-workspa-aae0b-bar-Workspaces-context-menu-documentation/error-context.md": "de239c63a0b17f6f3309e5afd2c47428",
                "test-documentation-customi-38159-t-should-use-default-layout-documentation/video.webm": "4f190c86be532f2d044099011306a38e",
                "test-documentation-customi-38159-t-should-use-default-layout-documentation/default-terminal-position-single-actual.png": "5a0a2040f0fc5b1457986f3575117433",
                "test-documentation-customi-38159-t-should-use-default-layout-documentation/default-terminal-position-single-diff.png": "a042a221e77dcc4954a0fa4e912eee9b",
                "test-documentation-customi-38159-t-should-use-default-layout-documentation/error-context.md": "8e72e868618f8ac3052df7ccc1689e5a",
                "test-documentation-customi-38159-t-should-use-default-layout-documentation/default-terminal-position-single-expected.png": "0ef5ee2bada38346cc2df97b1e4d16f1",
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
