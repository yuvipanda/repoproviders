import pytest
from yarl import URL

from repoproviders.resolvers.doi import Doi, DoiResolver


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://example.com/something", None),
        # doi schema'd URI
        (
            "doi:10.7910/DVN/6ZXAGT/3YRRYJ",
            Doi(
                "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
            ),
        ),
        # handle schema'd URI
        (
            "hdl:11529/10016",
            Doi("https://data.cimmyt.org/dataset.xhtml?persistentId=hdl:11529/10016"),
        ),
        # For convenience, we do accept DOIs without a scheme
        (
            "10.7910/DVN/6ZXAGT/3YRRYJ",
            Doi(
                "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
            ),
        ),
        # But not handles without a scheme
        ("11529/10016", None),
        # Three DOI resolution URLs
        (
            "https://doi.org/10.7910/DVN/6ZXAGT/3YRRYJ",
            Doi(
                "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
            ),
        ),
        (
            "https://www.doi.org/10.7910/DVN/6ZXAGT/3YRRYJ",
            Doi(
                "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
            ),
        ),
        (
            "https://hdl.handle.net/10.7910/DVN/6ZXAGT/3YRRYJ",
            Doi(
                "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
            ),
        ),
    ),
)
async def test_doi(url, expected):
    doi = DoiResolver()
    assert await doi.resolve(URL(url)) == expected
