import pytest
from yarl import URL

from repoproviders.resolvers.base import Exists, MaybeExists
from repoproviders.resolvers.git import Git
from repoproviders.resolvers.guess import GuessResolver
from repoproviders.resolvers.urls import DataverseURL


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
        # A dataverse URL from a dataverse installation that is *not* in our well known list
        (
            "https://demo.dataverse.org/dataset.xhtml?persistentId=doi:10.70122/FK2/MBQA9G",
            MaybeExists(
                DataverseURL(
                    URL("https://demo.dataverse.org"),
                    URL(
                        "https://demo.dataverse.org/dataset.xhtml?persistentId=doi:10.70122/FK2/MBQA9G"
                    ),
                )
            ),
        ),
        # A dataverse URL that does exist in our list, but good to make sure guess works with it still
        (
            "https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/DVN/TJCLKP",
            MaybeExists(
                DataverseURL(
                    URL("https://dataverse.harvard.edu/"),
                    URL(
                        "https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/DVN/TJCLKP"
                    ),
                )
            ),
        ),
    ),
)
async def test_doi(url, expected):
    guess = GuessResolver()
    assert await guess.resolve(URL(url)) == expected
