import pytest
from yarl import URL

from repoproviders.resolvers.base import Exists
from repoproviders.resolvers.git import Git
from repoproviders.resolvers.guess import GuessResolver


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://example.com/something", None),
        # Try a raw git repo
        (
            "https://git.kernel.org/pub/scm/virt/kvm/kvm.git/",
            Exists(Git("https://git.kernel.org/pub/scm/virt/kvm/kvm.git/", "HEAD")),
        ),
        # A Codeberg repo
        (
            "https://codeberg.org/Codeberg/Documentation",
            Exists(Git("https://codeberg.org/Codeberg/Documentation", "HEAD")),
        ),
    ),
)
async def test_doi(url, expected):
    guess = GuessResolver()
    assert await guess.resolve(URL(url)) == expected
