import pytest
from yarl import URL

from repoproviders.resolvers.base import DoesNotExist, Exists
from repoproviders.resolvers.doi import DataverseResolver
from repoproviders.resolvers.urls import DataverseDataset, DataverseURL


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        # A dataset citation returns the dataset correctly
        (
            DataverseURL(
                URL("https://dataverse.harvard.edu"),
                URL(
                    "https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/DVN/TJCLKP"
                ),
            ),
            Exists(
                DataverseDataset(
                    URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/TJCLKP"
                )
            ),
        ),
        (
            DataverseURL(
                URL("https://dataverse.harvard.edu"),
                URL(
                    "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/TJCLKP"
                ),
            ),
            Exists(
                DataverseDataset(
                    URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/TJCLKP"
                )
            ),
        ),
        # Asking for specific files should give us the whole dataset they are a part of
        (
            DataverseURL(
                URL("https://dataverse.harvard.edu"),
                URL("https://dataverse.harvard.edu/api/access/datafile/3323458"),
            ),
            Exists(
                DataverseDataset(
                    URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/3MJ7IR"
                )
            ),
        ),
        (
            DataverseURL(
                URL("https://dataverse.harvard.edu"),
                URL(
                    "https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                ),
            ),
            Exists(
                DataverseDataset(
                    URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/6ZXAGT"
                )
            ),
        ),
        (
            DataverseURL(
                URL("https://dataverse.harvard.edu"),
                URL(
                    "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                ),
            ),
            Exists(
                DataverseDataset(
                    URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/6ZXAGT"
                )
            ),
        ),
        # Asking for datasets that don't exist should return DoesNotExist
        (
            DataverseURL(
                URL("https://dataverse.harvard.edu"),
                URL(
                    "https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/not-found"
                ),
            ),
            DoesNotExist(
                DataverseDataset,
                "doi:10.7910/not-found is neither a file nor a dataset in https://dataverse.harvard.edu",
            ),
        ),
        (
            DataverseURL(
                URL("https://dataverse.harvard.edu"),
                URL(
                    "https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/not-found"
                ),
            ),
            DoesNotExist(
                DataverseDataset,
                "doi:10.7910/not-found is neither a file nor a dataset in https://dataverse.harvard.edu",
            ),
        ),
        (
            DataverseURL(
                URL("https://dataverse.harvard.edu"),
                URL("https://dataverse.harvard.edu/api/access/datafile/0"),
            ),
            DoesNotExist(
                DataverseDataset,
                "No file with id 0 found in dataverse installation https://dataverse.harvard.edu",
            ),
        ),
        (
            DataverseURL(
                URL("https://dataverse.harvard.edu"),
                URL("https://dataverse.harvard.edu/blaaaah"),
            ),
            None,
        ),
        (
            DataverseURL(
                URL("https://dataverse.harvard.edu"),
                URL(
                    "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/not-found"
                ),
            ),
            DoesNotExist(
                DataverseDataset,
                "No file with id doi:10.7910/not-found found in dataverse installation https://dataverse.harvard.edu",
            ),
        ),
    ),
)
async def test_dataverse(url, expected):
    dv = DataverseResolver()
    assert await dv.resolve(url) == expected
