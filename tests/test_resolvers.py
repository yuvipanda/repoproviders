import pytest
from yarl import URL

from repoproviders.resolvers.base import NotFound
from repoproviders.resolvers.doi import (
    DataverseDataset,
    DataverseResolver,
    Doi,
    DoiResolver,
    FigshareDataset,
    FigshareInstallation,
    FigshareResolver,
    ImmutableFigshareDataset,
    ImmutableFigshareResolver,
    ZenodoDataset,
    ZenodoResolver,
)
from repoproviders.resolvers.git import (
    Git,
    GitHubResolver,
    ImmutableGit,
    ImmutableGitResolver,
)


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://example.com/something", None),
        # GitHub URLs that are not repos
        ("https://github.com/pyOpenSci", None),
        (
            "https://github.com/yuvipanda/repoproviders/actions/runs/12552733471/job/34999118812",
            None,
        ),
        ("https://github.com/yuvipanda/repoproviders/settings", None),
        ("https://github.com/jupyter/docker-stacks/pull/2194", None),
        # Simple github repo URL
        (
            "https://github.com/pyOpenSci/pyos-package-template",
            Git("https://github.com/pyOpenSci/pyos-package-template", "HEAD"),
        ),
        # Trailing slash normalized?
        (
            "https://github.com/pyOpenSci/pyos-package-template/",
            Git("https://github.com/pyOpenSci/pyos-package-template", "HEAD"),
        ),
        # blobs and tree
        (
            "https://github.com/pyOpenSci/pyos-package-template/tree/main/includes/licenses",
            Git("https://github.com/pyOpenSci/pyos-package-template", "main"),
        ),
        (
            "https://github.com/pyOpenSci/pyos-package-template/tree/original-cookie/docs",
            Git(
                "https://github.com/pyOpenSci/pyos-package-template", "original-cookie"
            ),
        ),
        (
            "https://github.com/pyOpenSci/pyos-package-template/blob/b912433bfae541972c83529359f4181ef0fe9b67/README.md",
            Git(
                "https://github.com/pyOpenSci/pyos-package-template",
                ref="b912433bfae541972c83529359f4181ef0fe9b67",
            ),
        ),
        (
            "https://github.com/yuvipanda/does-not-exist-e43",
            Git(repo="https://github.com/yuvipanda/does-not-exist-e43", ref="HEAD"),
        ),
    ),
)
async def test_github(url, expected):
    gh = GitHubResolver()
    assert await gh.resolve(URL(url)) == expected


@pytest.mark.parametrize(
    ("question", "expected"),
    (
        # Random URL, not a git repo
        (Git("https://example.com/something", "HEAD"), NotFound()),
        # Resolve a tag
        (
            Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "0.8.0"),
            ImmutableGit(
                "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                "ada2170a2181ae1760d85eab74e5264d0c6bb67f",
            ),
        ),
        # Resolve a commit we know exists, although this isn't verified
        (
            Git(
                "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
            ),
            ImmutableGit(
                "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
            ),
        ),
        # Repo doesn't exist
        (
            Git(repo="https://github.com/yuvipanda/does-not-exist-e43", ref="HEAD"),
            NotFound(),
        ),
        # Ref doesn't exist
        (
            Git(
                "https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "does-not-exist"
            ),
            NotFound(),
        ),
    ),
)
async def test_immutable_git(question, expected):
    ig = ImmutableGitResolver()
    assert await ig.resolve(question) == expected


async def test_immutable_git_HEAD():
    """
    Extra test to test resolving HEAD, making sure it's the same as resolving "main".

    This can't be fixtured because HEAD and `mail` will keep mocing
    """
    ig = ImmutableGitResolver()
    assert (
        await ig.resolve(
            Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "main")
        )
    ) == (
        await ig.resolve(
            Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "main")
        )
    )


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