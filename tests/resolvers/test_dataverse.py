import pytest
from yarl import URL

from repoproviders.resolvers.base import NotFound
from repoproviders.resolvers.doi import DataverseDataset, DataverseResolver


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://example.com/something", None),
        # Dataverse URLs should wholly under the subpath URL
        ("https://dvn.library.ubc.ca/not-dvn/something-else", None),
        # A dataset citation returns the dataset correctly
        (
            "https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/DVN/TJCLKP",
            DataverseDataset(
                URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/TJCLKP"
            ),
        ),
        (
            "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/TJCLKP",
            DataverseDataset(
                URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/TJCLKP"
            ),
        ),
        # Asking for specific files should give us the whole dataset they are a part of
        (
            "https://dataverse.harvard.edu/api/access/datafile/3323458",
            DataverseDataset(
                URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/3MJ7IR"
            ),
        ),
        (
            "https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ",
            DataverseDataset(
                URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/6ZXAGT"
            ),
        ),
        (
            "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ",
            DataverseDataset(
                URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/6ZXAGT"
            ),
        ),
        # Asking for datasets that don't exist should return NotFound
        (
            "https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/not-found",
            NotFound(),
        ),
        (
            "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/not-found",
            NotFound(),
        ),
        ("https://dataverse.harvard.edu/api/access/datafile/0", NotFound()),
        ("https://dataverse.harvard.edu/blaaaah", NotFound()),
        (
            "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/not-found",
            NotFound(),
        ),
    ),
)
async def test_dataverse(url, expected):
    dv = DataverseResolver()
    assert await dv.resolve(URL(url)) == expected
