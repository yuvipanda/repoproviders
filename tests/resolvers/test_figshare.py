import pytest
from yarl import URL

from repoproviders.resolvers.base import NotFound
from repoproviders.resolvers.doi import (
    FigshareDataset,
    FigshareInstallation,
    FigshareResolver,
    ImmutableFigshareDataset,
    ImmutableFigshareResolver,
)


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://example.com/something", None),
        # A non-dataset URL
        ("https://figshare.com/browse", None),
        # A non-dataset URL that looks suspiciously like a dataset URL
        (
            "https://figshare.com/collections/Risk_reduction_in_SARS-CoV-2_infection_and_reinfection_conferred_by_humoral_antibody_levels_among_essential_workers_during_Omicron_predominance/7605487",
            None,
        ),
        # Some old school URLs
        (
            "https://figshare.com/articles/title/9782777",
            FigshareDataset(
                FigshareInstallation(
                    URL("https://figshare.com/"), URL("https://api.figshare.com/v2/")
                ),
                9782777,
                None,
            ),
        ),
        (
            "https://figshare.com/articles/title/9782777/2",
            FigshareDataset(
                FigshareInstallation(
                    URL("https://figshare.com/"), URL("https://api.figshare.com/v2/")
                ),
                9782777,
                2,
            ),
        ),
        # New style URLs
        (
            "https://figshare.com/articles/code/Binder-ready_openSenseMap_Analysis/9782777",
            FigshareDataset(
                FigshareInstallation(
                    URL("https://figshare.com/"), URL("https://api.figshare.com/v2/")
                ),
                9782777,
                None,
            ),
        ),
        (
            "https://figshare.com/articles/code/Binder-ready_openSenseMap_Analysis/9782777/3",
            FigshareDataset(
                FigshareInstallation(
                    URL("https://figshare.com/"), URL("https://api.figshare.com/v2/")
                ),
                9782777,
                3,
            ),
        ),
    ),
)
async def test_figshare(url, expected):
    fs = FigshareResolver()
    assert await fs.resolve(URL(url)) == expected


@pytest.mark.parametrize(
    ("question", "expected"),
    (
        (
            FigshareDataset(
                FigshareInstallation(
                    URL("https://figshare.com/"), URL("https://api.figshare.com/v2/")
                ),
                9782777,
                None,
            ),
            ImmutableFigshareDataset(
                FigshareInstallation(
                    URL("https://figshare.com/"), URL("https://api.figshare.com/v2/")
                ),
                9782777,
                3,
            ),
        ),
        (
            FigshareDataset(
                FigshareInstallation(
                    URL("https://figshare.com/"), URL("https://api.figshare.com/v2/")
                ),
                9782777,
                2,
            ),
            ImmutableFigshareDataset(
                FigshareInstallation(
                    URL("https://figshare.com/"), URL("https://api.figshare.com/v2/")
                ),
                9782777,
                2,
            ),
        ),
        # Non existent things
        (
            FigshareDataset(
                FigshareInstallation(
                    URL("https://figshare.com/"), URL("https://api.figshare.com/v2/")
                ),
                97827778384384634634634863463434343,
                None,
            ),
            NotFound(),
        ),
    ),
)
async def test_immutable_figshare(question, expected):
    ifs = ImmutableFigshareResolver()
    assert await ifs.resolve(question) == expected
