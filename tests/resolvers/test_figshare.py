import pytest
from yarl import URL

from repoproviders.resolvers.base import DoesNotExist, Exists, MaybeExists
from repoproviders.resolvers.doi import FigshareResolver, ImmutableFigshareResolver
from repoproviders.resolvers.repos import (
    FigshareDataset,
    FigshareInstallation,
    FigshareURL,
    ImmutableFigshareDataset,
)


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        # A non-dataset URL
        (
            FigshareURL(
                FigshareInstallation(
                    URL("https://figshare.com/"),
                    URL("https://api.figshare.com/v2/"),
                ),
                URL("https://figshare.com/browse"),
            ),
            None,
        ),
        # A non-dataset URL that looks suspiciously like a dataset URL
        (
            FigshareURL(
                FigshareInstallation(
                    URL("https://figshare.com/"),
                    URL("https://api.figshare.com/v2/"),
                ),
                URL(
                    "https://figshare.com/collections/Risk_reduction_in_SARS-CoV-2_infection_and_reinfection_conferred_by_humoral_antibody_levels_among_essential_workers_during_Omicron_predominance/7605487",
                ),
            ),
            None,
        ),
        # Some old school URLs
        (
            FigshareURL(
                FigshareInstallation(
                    URL("https://figshare.com/"),
                    URL("https://api.figshare.com/v2/"),
                ),
                URL(
                    "https://figshare.com/articles/title/9782777",
                ),
            ),
            MaybeExists(
                FigshareDataset(
                    FigshareInstallation(
                        URL("https://figshare.com/"),
                        URL("https://api.figshare.com/v2/"),
                    ),
                    9782777,
                    None,
                )
            ),
        ),
        (
            FigshareURL(
                FigshareInstallation(
                    URL("https://figshare.com/"),
                    URL("https://api.figshare.com/v2/"),
                ),
                URL(
                    "https://figshare.com/articles/title/9782777/2",
                ),
            ),
            MaybeExists(
                FigshareDataset(
                    FigshareInstallation(
                        URL("https://figshare.com/"),
                        URL("https://api.figshare.com/v2/"),
                    ),
                    9782777,
                    2,
                )
            ),
        ),
        # New style URLs
        (
            FigshareURL(
                FigshareInstallation(
                    URL("https://figshare.com/"),
                    URL("https://api.figshare.com/v2/"),
                ),
                URL(
                    "https://figshare.com/articles/code/Binder-ready_openSenseMap_Analysis/9782777",
                ),
            ),
            MaybeExists(
                FigshareDataset(
                    FigshareInstallation(
                        URL("https://figshare.com/"),
                        URL("https://api.figshare.com/v2/"),
                    ),
                    9782777,
                    None,
                )
            ),
        ),
        (
            FigshareURL(
                FigshareInstallation(
                    URL("https://figshare.com/"),
                    URL("https://api.figshare.com/v2/"),
                ),
                URL(
                    "https://figshare.com/articles/code/Binder-ready_openSenseMap_Analysis/9782777/3",
                ),
            ),
            MaybeExists(
                FigshareDataset(
                    FigshareInstallation(
                        URL("https://figshare.com/"),
                        URL("https://api.figshare.com/v2/"),
                    ),
                    9782777,
                    3,
                )
            ),
        ),
    ),
)
async def test_figshare(url, expected, log):
    fs = FigshareResolver()
    assert await fs.resolve(url, log) == expected


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
            Exists(
                ImmutableFigshareDataset(
                    FigshareInstallation(
                        URL("https://figshare.com/"),
                        URL("https://api.figshare.com/v2/"),
                    ),
                    9782777,
                    3,
                )
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
            MaybeExists(
                ImmutableFigshareDataset(
                    FigshareInstallation(
                        URL("https://figshare.com/"),
                        URL("https://api.figshare.com/v2/"),
                    ),
                    9782777,
                    2,
                )
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
            DoesNotExist(
                ImmutableFigshareDataset,
                "Article ID 97827778384384634634634863463434343 not found on figshare installation https://figshare.com/",
            ),
        ),
    ),
)
async def test_immutable_figshare(question, expected, log):
    ifs = ImmutableFigshareResolver()
    assert await ifs.resolve(question, log) == expected
