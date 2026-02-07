import pytest
from yarl import URL

from repoproviders.resolvers.base import Exists, MaybeExists
from repoproviders.resolvers.feature_detect import FeatureDetectResolver
from repoproviders.resolvers.git import Git
from repoproviders.resolvers.repos import CompressedFile, DataverseURL


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
        # A ZIP file with working etag
        (
            "https://codeload.github.com/jupyter/governance/zip/31ca8204d8ca6366d968de2c10bcf5572f7a048e",
            Exists(
                CompressedFile(
                    URL(
                        "https://codeload.github.com/jupyter/governance/zip/31ca8204d8ca6366d968de2c10bcf5572f7a048e"
                    ),
                    mime_type="application/zip",
                    etag='"bf3c60d9118d8e1317c0852e8b2e3e9b7a9176413f512262b08ddc7a7659d804"',
                )
            ),
        ),
        # A ZIP file *without* working etag, which we don't support now
        ("https://sandbox.zenodo.org/api/records/436825/files-archive", None),
    ),
)
async def test_doi(url, expected):
    fd = FeatureDetectResolver()
    assert await fd.resolve(URL(url)) == expected
