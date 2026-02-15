import pytest
from yarl import URL

from repoproviders.resolvers.base import MaybeExists
from repoproviders.resolvers.git import Git, GitUrlResolver


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        # Not a git url
        ("https://example.com/something", None),
        # Not a real repo, but looks like one
        (
            "git+https://example.com/something",
            MaybeExists(Git("https://example.com/something", "HEAD")),
        ),
        (
            "git+ssh://example.com/something",
            MaybeExists(Git("ssh://example.com/something", "HEAD")),
        ),
        # With a ref
        (
            "git+https://github.com/yuvipanda/requirements@main",
            MaybeExists(Git("https://github.com/yuvipanda/requirements", "main")),
        ),
        # With edge case refs
        (
            "git+https://github.com/yuvipanda/requirements@tag/something",
            MaybeExists(
                Git("https://github.com/yuvipanda/requirements", "tag/something")
            ),
        ),
        (
            "git+https://yuvipanda@github.com/yuvipanda/requirements@tag/something",
            MaybeExists(
                Git(
                    "https://yuvipanda@github.com/yuvipanda/requirements",
                    "tag/something",
                )
            ),
        ),
        (
            "git+https://yuvipanda@github.com/yuvipanda/requirements@tag@something",
            MaybeExists(
                Git(
                    "https://yuvipanda@github.com/yuvipanda/requirements",
                    "tag@something",
                )
            ),
        ),
    ),
)
async def test_giturl(url, expected, log):
    gu = GitUrlResolver()
    assert await gu.resolve(URL(url), log) == expected
