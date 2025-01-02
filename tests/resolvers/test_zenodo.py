import pytest
from yarl import URL

from repoproviders.resolvers.base import NotFound
from repoproviders.resolvers.doi import ZenodoDataset, ZenodoResolver


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://example.com/something", None),
        # A non-dataset URL
        ("https://data.caltech.edu/communities", None),
        # Simple /record and /records
        (
            "https://zenodo.org/record/3232985",
            ZenodoDataset(URL("https://zenodo.org/"), "3232985"),
        ),
        (
            "https://zenodo.org/records/3232985",
            ZenodoDataset(URL("https://zenodo.org/"), "3232985"),
        ),
        # Note we normalize output to have the HTTPS URL, even if we're passed in the HTTP URL
        (
            "http://zenodo.org/record/3232985",
            ZenodoDataset(URL("https://zenodo.org/"), "3232985"),
        ),
        (
            "https://zenodo.org/records/3232985",
            ZenodoDataset(URL("https://zenodo.org/"), "3232985"),
        ),
        # A non-zenodo URL
        (
            "https://data.caltech.edu/records/996aw-mf266",
            ZenodoDataset(URL("https://data.caltech.edu/"), "996aw-mf266"),
        ),
        # A doi reference
        (
            "https://zenodo.org/doi/10.5281/zenodo.805993",
            ZenodoDataset(URL("https://zenodo.org/"), recordId="14007206"),
        ),
        # A doi reference to a bad doi
        ("https://zenodo.org/doi/10.5281/zdo.805993", NotFound()),
    ),
)
async def test_zenodo(url, expected):
    zr = ZenodoResolver()
    assert await zr.resolve(URL(url)) == expected
