import pytest
from yarl import URL

from repoproviders.resolvers import resolve
from repoproviders.resolvers.base import NotFound
from repoproviders.resolvers.doi import (
    DataverseDataset,
    Doi,
    FigshareDataset,
    FigshareInstallation,
    ImmutableFigshareDataset,
    ZenodoDataset,
)
from repoproviders.resolvers.git import Git, ImmutableGit


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://example.com/something", []),
        # GitHub URLs that are not repos
        ("https://github.com/pyOpenSci", []),
        (
            "https://github.com/yuvipanda/repoproviders/actions/runs/12552733471/job/34999118812",
            [],
        ),
        ("https://github.com/yuvipanda/repoproviders/settings", []),
        ("https://github.com/jupyter/docker-stacks/pull/2194", []),
        # Simple github repo URL
        (
            "https://github.com/pyOpenSci/pyos-package-template",
            [Git("https://github.com/pyOpenSci/pyos-package-template", "HEAD")],
        ),
        # Trailing slash normalized?
        (
            "https://github.com/pyOpenSci/pyos-package-template/",
            [Git("https://github.com/pyOpenSci/pyos-package-template", "HEAD")],
        ),
        # blobs and tree
        (
            "https://github.com/pyOpenSci/pyos-package-template/tree/main/includes/licenses",
            [Git("https://github.com/pyOpenSci/pyos-package-template", "main")],
        ),
        (
            "https://github.com/pyOpenSci/pyos-package-template/tree/original-cookie/docs",
            [
                Git(
                    "https://github.com/pyOpenSci/pyos-package-template",
                    "original-cookie",
                )
            ],
        ),
        (
            "https://github.com/pyOpenSci/pyos-package-template/blob/b912433bfae541972c83529359f4181ef0fe9b67/README.md",
            [
                Git(
                    "https://github.com/pyOpenSci/pyos-package-template",
                    ref="b912433bfae541972c83529359f4181ef0fe9b67",
                )
            ],
        ),
        # Random URL, not a git repo
        (Git("https://example.com/something", "HEAD"), [NotFound()]),
        # Resolve a tag
        (
            Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "0.8.0"),
            [
                ImmutableGit(
                    "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                    "ada2170a2181ae1760d85eab74e5264d0c6bb67f",
                )
            ],
        ),
        # Resolve a commit we know exists, although this isn't verified
        (
            Git(
                "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
            ),
            [
                ImmutableGit(
                    "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                    "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
                )
            ],
        ),
        (
            Git(
                "https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "does-not-exist"
            ),
            [NotFound()],
        ),
    ),
)
async def test_resolve(url, expected):
    assert await resolve(url, False) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://example.com/something", []),
        # doi schema'd URI
        (
            "doi:10.7910/DVN/6ZXAGT/3YRRYJ",
            [
                Doi(
                    "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                )
            ],
        ),
        # handle schema'd URI
        (
            "hdl:11529/10016",
            [Doi("https://data.cimmyt.org/dataset.xhtml?persistentId=hdl:11529/10016")],
        ),
        # For convenience, we do accept DOIs without a scheme
        (
            "10.7910/DVN/6ZXAGT/3YRRYJ",
            [
                Doi(
                    "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                )
            ],
        ),
        # But not handles without a scheme
        ("11529/10016", []),
        # Three DOI resolution URLs
        (
            "https://doi.org/10.7910/DVN/6ZXAGT/3YRRYJ",
            [
                Doi(
                    "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                )
            ],
        ),
        (
            "https://www.doi.org/10.7910/DVN/6ZXAGT/3YRRYJ",
            [
                Doi(
                    "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                )
            ],
        ),
        (
            "https://hdl.handle.net/10.7910/DVN/6ZXAGT/3YRRYJ",
            [
                Doi(
                    "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                )
            ],
        ),
    ),
)
async def test_norecurse(url, expected):
    assert await resolve(URL(url), False) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        # doi schema'd URI
        (
            "doi:10.7910/DVN/6ZXAGT/3YRRYJ",
            [
                Doi(
                    "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                ),
                DataverseDataset(
                    URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/6ZXAGT"
                ),
            ],
        ),
        # handle schema'd URI
        (
            "hdl:11529/10016",
            [
                Doi(
                    "https://data.cimmyt.org/dataset.xhtml?persistentId=hdl:11529/10016"
                ),
                DataverseDataset(URL("http://data.cimmyt.org/"), "hdl:11529/10016"),
            ],
        ),
        # For convenience, we do accept DOIs without a scheme
        (
            "10.7910/DVN/6ZXAGT",
            [
                Doi(
                    "https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/DVN/6ZXAGT"
                ),
                DataverseDataset(
                    URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/6ZXAGT"
                ),
            ],
        ),
        # Something that's only a DOI, and won't resolve further
        (
            "10.1126/science.aar3646",
            [Doi("https://www.science.org/doi/10.1126/science.aar3646")],
        ),
        # GitHub URLs that recurse into ImmutableGit
        (
            "https://github.com/jupyterhub/zero-to-jupyterhub-k8s/tree/f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
            [
                Git(
                    "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                    "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
                ),
                ImmutableGit(
                    "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                    "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
                ),
            ],
        ),
        (
            "https://github.com/jupyterhub/zero-to-jupyterhub-k8s/tree/0.8.0",
            [
                Git(
                    "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                    "0.8.0",
                ),
                ImmutableGit(
                    "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                    "ada2170a2181ae1760d85eab74e5264d0c6bb67f",
                ),
            ],
        ),
        # Git URLs that recurse into ImmutableGit
        (
            "git+https://github.com/jupyterhub/zero-to-jupyterhub-k8s@f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
            [
                Git(
                    "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                    "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
                ),
                ImmutableGit(
                    "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                    "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
                ),
            ],
        ),
        (
            "git+https://github.com/jupyterhub/zero-to-jupyterhub-k8s@0.8.0",
            [
                Git(
                    "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                    "0.8.0",
                ),
                ImmutableGit(
                    "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                    "ada2170a2181ae1760d85eab74e5264d0c6bb67f",
                ),
            ],
        ),
        (
            "10.5281/zenodo.3232985",
            [
                Doi("https://zenodo.org/record/3232985"),
                ZenodoDataset(URL("https://zenodo.org/"), "3232985"),
            ],
        ),
        (
            "https://doi.org/10.6084/m9.figshare.9782777.v3",
            [
                Doi(
                    "https://figshare.com/articles/Binder-ready_openSenseMap_Analysis/9782777/3"
                ),
                FigshareDataset(
                    FigshareInstallation(
                        URL("https://figshare.com/"),
                        URL("https://api.figshare.com/v2/"),
                    ),
                    9782777,
                    3,
                ),
                ImmutableFigshareDataset(
                    FigshareInstallation(
                        URL("https://figshare.com/"),
                        URL("https://api.figshare.com/v2/"),
                    ),
                    9782777,
                    3,
                ),
            ],
        ),
        (
            "https://figshare.com/articles/Binder-ready_openSenseMap_Analysis/9782777",
            [
                FigshareDataset(
                    FigshareInstallation(
                        URL("https://figshare.com/"),
                        URL("https://api.figshare.com/v2/"),
                    ),
                    9782777,
                    None,
                ),
                ImmutableFigshareDataset(
                    FigshareInstallation(
                        URL("https://figshare.com/"),
                        URL("https://api.figshare.com/v2/"),
                    ),
                    9782777,
                    3,
                ),
            ],
        ),
        # A zenodo doi that uses the /doi redirect
        (
            "https://doi.org/10.5281/zenodo.805993",
            [
                Doi(url="https://zenodo.org/doi/10.5281/zenodo.805993"),
                ZenodoDataset(URL("https://zenodo.org/"), "14007206"),
            ],
        ),
    ),
)
async def test_recurse(url, expected):
    assert await resolve(URL(url), True) == expected
