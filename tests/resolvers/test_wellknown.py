import pytest
from yarl import URL

from repoproviders.resolvers.base import MaybeExists
from repoproviders.resolvers.rclone import GoogleDriveFolder
from repoproviders.resolvers.repos import (
    DataverseURL,
    Doi,
    FigshareInstallation,
    FigshareURL,
    GistURL,
    GitHubURL,
    GitLabURL,
    HydroshareDataset,
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
        (
            "https://gist.github.com/yuvipanda",
            MaybeExists(
                GistURL(
                    URL("https://gist.github.com"),
                    URL("https://gist.github.com/yuvipanda"),
                )
            ),
        ),
        (
            "https://gist.github.com/JakeWharton/5423616",
            MaybeExists(
                GistURL(
                    URL("https://gist.github.com"),
                    URL("https://gist.github.com/JakeWharton/5423616"),
                )
            ),
        ),
        (
            # We support directory links
            "https://drive.google.com/drive/folders/1o3okM5hYOgUGHYipyjiblEzbp29UX9cF",
            MaybeExists(GoogleDriveFolder("1o3okM5hYOgUGHYipyjiblEzbp29UX9cF")),
        ),
        (
            # We don't support file links
            "https://drive.google.com/file/d/110LCoTV6NM7YpMc7MqooQ9pJ0PhsOzFY/view?usp=drive_link",
            None,
        ),
        (
            # Support URLs without www.
            "https://hydroshare.org/resource/76502ab28c5744f98e2bbad5155e39c7/",
            MaybeExists(HydroshareDataset("76502ab28c5744f98e2bbad5155e39c7")),
        ),
        (
            # Support URLs with www.
            "https://www.hydroshare.org/resource/76502ab28c5744f98e2bbad5155e39c7/",
            MaybeExists(HydroshareDataset("76502ab28c5744f98e2bbad5155e39c7")),
        ),
        (
            # Handle lack of trailing /
            "https://www.hydroshare.org/resource/76502ab28c5744f98e2bbad5155e39c7",
            MaybeExists(HydroshareDataset("76502ab28c5744f98e2bbad5155e39c7")),
        ),
        (
            # Random hydroshare URLs don't work
            "https://hydroshare.org/search/",
            None,
        ),
    ),
)
async def test_doi(question, expected, log):
    wk = WellKnownProvidersResolver()
    if isinstance(question, str):
        question = URL(question)
    assert await wk.resolve(question, log) == expected
