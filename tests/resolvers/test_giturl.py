import pytest
from yarl import URL

from repoproviders.resolvers.git import Git, GitUrlResolver


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        # Not a git url
        ("https://example.com/something", None),
        # Not a real repo, but looks like one
        (
            "git+https://example.com/something",
            Git("https://example.com/something", "HEAD"),
        ),
        ("git+ssh://example.com/something", Git("ssh://example.com/something", "HEAD")),
        # With a ref
        (
            "git+https://github.com/yuvipanda/requirements@main",
            Git("https://github.com/yuvipanda/requirements", "main"),
        ),
        # With edge case refs
        (
            "git+https://github.com/yuvipanda/requirements@tag/something",
            Git("https://github.com/yuvipanda/requirements", "tag/something"),
        ),
        (
            "git+https://yuvipanda@github.com/yuvipanda/requirements@tag/something",
            Git("https://yuvipanda@github.com/yuvipanda/requirements", "tag/something"),
        ),
        (
            "git+https://yuvipanda@github.com/yuvipanda/requirements@tag@something",
            Git("https://yuvipanda@github.com/yuvipanda/requirements", "tag@something"),
        ),
    ),
)
async def test_giturl(url, expected):
    gu = GitUrlResolver()
    assert await gu.resolve(URL(url)) == expected
