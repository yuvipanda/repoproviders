import pytest
from yarl import URL

from repoproviders.resolvers.base import DoesNotExist, MaybeExists
from repoproviders.resolvers.doi import ZenodoResolver
from repoproviders.resolvers.repos import ZenodoDataset, ZenodoURL


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        # A valid Zenodo URL that isn't actually a dataset
        (
            ZenodoURL(URL("https://zenodo.org"), URL("https://zenodo.org/communities")),
            None,
        ),
        # Simple /record and /records
        (
            ZenodoURL(
                URL("https://zenodo.org"), URL("https://zenodo.org/record/3232985")
            ),
            MaybeExists(ZenodoDataset(URL("https://zenodo.org/"), "3232985")),
        ),
        (
            ZenodoURL(
                URL("https://zenodo.org"), URL("https://zenodo.org/records/3232985")
            ),
            MaybeExists(ZenodoDataset(URL("https://zenodo.org/"), "3232985")),
        ),
        # Note we normalize output to have the HTTPS URL, even if we're passed in the HTTP URL
        (
            ZenodoURL(
                URL("https://zenodo.org"), URL("http://zenodo.org/record/3232985")
            ),
            MaybeExists(ZenodoDataset(URL("https://zenodo.org/"), "3232985")),
        ),
        (
            ZenodoURL(
                URL("https://zenodo.org"), URL("https://zenodo.org/records/3232985")
            ),
            MaybeExists(ZenodoDataset(URL("https://zenodo.org/"), "3232985")),
        ),
        # A non-zenodo.org URL
        (
            ZenodoURL(
                URL("https://data.caltech.edu"),
                URL("https://data.caltech.edu/records/996aw-mf266"),
            ),
            MaybeExists(ZenodoDataset(URL("https://data.caltech.edu/"), "996aw-mf266")),
        ),
        # A doi reference
        (
            ZenodoURL(
                URL("https://zenodo.org"),
                URL("https://zenodo.org/doi/10.5281/zenodo.805993"),
            ),
            MaybeExists(ZenodoDataset(URL("https://zenodo.org/"), recordId="14007206")),
        ),
        # A doi reference to a bad doi
        (
            ZenodoURL(
                URL("https://zenodo.org"),
                URL("https://zenodo.org/doi/10.5281/zdo.805993"),
            ),
            DoesNotExist(
                ZenodoDataset,
                "https://zenodo.org/doi/10.5281/zdo.805993 is not a valid Zenodo DOI URL",
            ),
        ),
    ),
)
async def test_zenodo(url, expected, log):
    zr = ZenodoResolver()
    assert await zr.resolve(url, log) == expected
