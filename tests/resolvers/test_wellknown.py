import pytest
from yarl import URL

from repoproviders.resolvers.base import MaybeExists
from repoproviders.resolvers.repos import (
    DataverseURL,
    Doi,
    FigshareInstallation,
    FigshareURL,
    GitHubURL,
    GitLabURL,
    ZenodoURL,
)
from repoproviders.resolvers.wellknown import WellKnownProvidersResolver


@pytest.mark.parametrize(
    ("question", "expected"),
    (
        ("https://example.com/something", None),
        # Try a raw git repo - this should be only detected by feature detector
        (
            "https://git.kernel.org/pub/scm/virt/kvm/kvm.git/",
            None,
        ),
        # A github URL even if it's not actually a valid repo
        (
            "https://github.com/settings",
            MaybeExists(
                GitHubURL(URL("https://github.com"), URL("https://github.com/settings"))
            ),
        ),
        # A dataverse URL that doesn't exist in our well known set, so should be None
        (
            "https://demo.dataverse.org/dataset.xhtml?persistentId=doi:10.70122/FK2/MBQA9G",
            None,
        ),
        (
            "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/TJCLKP",
            MaybeExists(
                DataverseURL(
                    URL("https://dataverse.harvard.edu"),
                    URL(
                        "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/TJCLKP"
                    ),
                )
            ),
        ),
        (
            Doi(URL("https://zenodo.org/record/3232985")),
            MaybeExists(
                ZenodoURL(
                    URL("https://zenodo.org"),
                    URL("https://zenodo.org/record/3232985"),
                )
            ),
        ),
        (
            "https://zenodo.org/settings",
            MaybeExists(
                ZenodoURL(
                    URL("https://zenodo.org"),
                    URL("https://zenodo.org/settings"),
                )
            ),
        ),
        (
            "https://figshare.com/browse",
            MaybeExists(
                FigshareURL(
                    FigshareInstallation(
                        URL("https://figshare.com/"),
                        URL("https://api.figshare.com/v2/"),
                    ),
                    URL("https://figshare.com/browse"),
                )
            ),
        ),
        (
            "https://gitlab.com/browse",
            MaybeExists(
                GitLabURL(URL("https://gitlab.com"), URL("https://gitlab.com/browse"))
            ),
        ),
    ),
)
async def test_doi(question, expected):
    wk = WellKnownProvidersResolver()
    if isinstance(question, str):
        question = URL(question)
    assert await wk.resolve(question) == expected
