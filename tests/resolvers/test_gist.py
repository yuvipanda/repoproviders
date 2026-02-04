import pytest
from yarl import URL

from repoproviders.resolvers.base import MaybeExists
from repoproviders.resolvers.git import GistResolver, Git
from repoproviders.resolvers.repos import GistURL


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        # Gist URLs that aren't gists
        (
            GistURL(
                URL("https://gist.github.com"), URL("https://gist.github.com/yuvipanda")
            ),
            None,
        ),
        # We don't support revisions yet
        (
            GistURL(
                URL("https://gist.github.com"),
                URL("https://gist.github.com/JakeWharton/5423616/revisions"),
            ),
            None,
        ),
        # An actual gist
        (
            GistURL(
                URL("https://gist.github.com"),
                URL("https://gist.github.com/JakeWharton/5423616"),
            ),
            MaybeExists(
                repo=Git(
                    repo="https://gist.github.com/JakeWharton/5423616",
                    ref="HEAD",
                )
            ),
        ),
    ),
)
async def test_gist(url, expected):
    gh = GistResolver()
    assert await gh.resolve(url) == expected
