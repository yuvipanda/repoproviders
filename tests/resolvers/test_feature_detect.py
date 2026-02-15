import pytest
from yarl import URL

from repoproviders.resolvers.base import Exists, MaybeExists
from repoproviders.resolvers.feature_detect import FeatureDetectResolver
from repoproviders.resolvers.git import Git
from repoproviders.resolvers.repos import CKANDataset, DataverseURL


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
        # A working CKAN instance
        (
            "https://catalog.data.gov/dataset/authorizations-from-10-01-2006-thru-12-31-2022",
            MaybeExists(
                CKANDataset(
                    URL("https://catalog.data.gov"),
                    "authorizations-from-10-01-2006-thru-12-31-2022",
                )
            ),
        ),
        # Looks like, but isn't actually a CKAN dataset
        ("https://catalog.data.gov/dataset/", None),
        # A CKAN instance with a base_url
        (
            "https://open.canada.ca/data/en/dataset/90fed587-1364-4f33-a9ee-208181dc0b97",
            MaybeExists(
                CKANDataset(
                    URL("https://open.canada.ca/data/en"),
                    "90fed587-1364-4f33-a9ee-208181dc0b97",
                )
            ),
        ),
    ),
)
async def test_doi(url, expected, log):
    fd = FeatureDetectResolver()
    assert await fd.resolve(URL(url), log) == expected
