import pytest
from yarl import URL

from repoproviders.resolvers import resolve
from repoproviders.resolvers.base import DoesNotExist, Exists, MaybeExists
from repoproviders.resolvers.git import Git, ImmutableGit
from repoproviders.resolvers.urls import (
    DataverseDataset,
    DataverseURL,
    Doi,
    FigshareDataset,
    FigshareInstallation,
    FigshareURL,
    GitHubURL,
    ImmutableFigshareDataset,
    ZenodoDataset,
    ZenodoURL,
)


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://example.com/something", []),
        # GitHub URLs that are not repos, but are still GitHub URLs
        (
            "https://github.com/pyOpenSci",
            [
                MaybeExists(
                    GitHubURL(
                        URL("https://github.com"), URL("https://github.com/pyOpenSci")
                    )
                )
            ],
        ),
        (
            "https://github.com/yuvipanda/repoproviders/actions/runs/12552733471/job/34999118812",
            [
                MaybeExists(
                    GitHubURL(
                        URL("https://github.com"),
                        URL(
                            "https://github.com/yuvipanda/repoproviders/actions/runs/12552733471/job/34999118812"
                        ),
                    )
                )
            ],
        ),
        (
            "https://github.com/yuvipanda/repoproviders/settings",
            [
                MaybeExists(
                    GitHubURL(
                        URL("https://github.com"),
                        URL("https://github.com/yuvipanda/repoproviders/settings"),
                    )
                )
            ],
        ),
        (
            "https://github.com/jupyter/docker-stacks/pull/2194",
            [
                MaybeExists(
                    GitHubURL(
                        URL("https://github.com"),
                        URL("https://github.com/jupyter/docker-stacks/pull/2194"),
                    )
                )
            ],
        ),
        # Simple github repo URL that are actual repos
        (
            GitHubURL(
                URL("https://github.com"),
                URL("https://github.com/pyOpenSci/pyos-package-template"),
            ),
            [
                MaybeExists(
                    Git("https://github.com/pyOpenSci/pyos-package-template", "HEAD")
                )
            ],
        ),
        # Trailing slash normalized?
        (
            GitHubURL(
                URL("https://github.com"),
                URL("https://github.com/pyOpenSci/pyos-package-template/"),
            ),
            [
                MaybeExists(
                    Git("https://github.com/pyOpenSci/pyos-package-template", "HEAD")
                )
            ],
        ),
        # blobs and tree
        (
            GitHubURL(
                URL("https://github.com"),
                URL(
                    "https://github.com/pyOpenSci/pyos-package-template/tree/main/includes/licenses"
                ),
            ),
            [
                MaybeExists(
                    Git("https://github.com/pyOpenSci/pyos-package-template", "main")
                )
            ],
        ),
        (
            GitHubURL(
                URL("https://github.com"),
                URL(
                    "https://github.com/pyOpenSci/pyos-package-template/tree/original-cookie/docs"
                ),
            ),
            [
                MaybeExists(
                    Git(
                        "https://github.com/pyOpenSci/pyos-package-template",
                        "original-cookie",
                    )
                )
            ],
        ),
        (
            GitHubURL(
                URL("https://github.com"),
                URL(
                    "https://github.com/pyOpenSci/pyos-package-template/blob/b912433bfae541972c83529359f4181ef0fe9b67/README.md"
                ),
            ),
            [
                MaybeExists(
                    Git(
                        "https://github.com/pyOpenSci/pyos-package-template",
                        ref="b912433bfae541972c83529359f4181ef0fe9b67",
                    )
                )
            ],
        ),
        # Random URL, not a git repo
        (
            Git("https://example.com/something", "HEAD"),
            [
                DoesNotExist(
                    ImmutableGit,
                    "Could not access git repository at https://example.com/something",
                )
            ],
        ),
        # Resolve a tag
        (
            Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "0.8.0"),
            [
                Exists(
                    ImmutableGit(
                        "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                        "ada2170a2181ae1760d85eab74e5264d0c6bb67f",
                    )
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
                MaybeExists(
                    ImmutableGit(
                        "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                        "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
                    )
                )
            ],
        ),
        (
            Git(
                "https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "does-not-exist"
            ),
            [
                DoesNotExist(
                    ImmutableGit,
                    "No ref does-not-exist found in repo https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                )
            ],
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
                Exists(
                    Doi(
                        URL(
                            "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                        )
                    )
                )
            ],
        ),
        # handle schema'd URI
        (
            "hdl:11529/10016",
            [
                Exists(
                    Doi(
                        URL(
                            "https://data.cimmyt.org/dataset.xhtml?persistentId=hdl:11529/10016"
                        )
                    )
                )
            ],
        ),
        # For convenience, we do accept DOIs without a scheme
        (
            "10.7910/DVN/6ZXAGT/3YRRYJ",
            [
                Exists(
                    Doi(
                        URL(
                            "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                        )
                    )
                )
            ],
        ),
        # But not handles without a scheme
        ("11529/10016", []),
        # Three DOI resolution URLs
        (
            "https://doi.org/10.7910/DVN/6ZXAGT/3YRRYJ",
            [
                Exists(
                    Doi(
                        URL(
                            "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                        )
                    )
                )
            ],
        ),
        (
            "https://www.doi.org/10.7910/DVN/6ZXAGT/3YRRYJ",
            [
                Exists(
                    Doi(
                        URL(
                            "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                        )
                    )
                )
            ],
        ),
        (
            "https://hdl.handle.net/10.7910/DVN/6ZXAGT/3YRRYJ",
            [
                Exists(
                    Doi(
                        URL(
                            "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                        )
                    )
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
                Exists(
                    Doi(
                        URL(
                            "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                        )
                    )
                ),
                MaybeExists(
                    DataverseURL(
                        URL("https://dataverse.harvard.edu"),
                        URL(
                            "https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ"
                        ),
                    ),
                ),
                Exists(
                    DataverseDataset(
                        URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/6ZXAGT"
                    )
                ),
            ],
        ),
        # handle schema'd URI
        (
            "hdl:11529/10016",
            [
                Exists(
                    Doi(
                        URL(
                            "https://data.cimmyt.org/dataset.xhtml?persistentId=hdl:11529/10016"
                        )
                    )
                ),
                MaybeExists(
                    DataverseURL(
                        URL("https://data.cimmyt.org"),
                        URL(
                            "https://data.cimmyt.org/dataset.xhtml?persistentId=hdl:11529/10016"
                        ),
                    ),
                ),
                Exists(
                    DataverseDataset(URL("https://data.cimmyt.org"), "hdl:11529/10016")
                ),
            ],
        ),
        # For convenience, we do accept DOIs without a scheme
        (
            "10.7910/DVN/6ZXAGT",
            [
                Exists(
                    Doi(
                        URL(
                            "https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/DVN/6ZXAGT"
                        )
                    )
                ),
                MaybeExists(
                    DataverseURL(
                        URL("https://dataverse.harvard.edu"),
                        URL(
                            "https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/DVN/6ZXAGT"
                        ),
                    ),
                ),
                Exists(
                    DataverseDataset(
                        URL("https://dataverse.harvard.edu"), "doi:10.7910/DVN/6ZXAGT"
                    )
                ),
            ],
        ),
        # Something that's only a DOI, and won't resolve further
        (
            "10.1126/science.aar3646",
            [Exists(Doi(URL("https://www.science.org/doi/10.1126/science.aar3646")))],
        ),
        # GitHub URLs that recurse into ImmutableGit
        (
            "https://github.com/jupyterhub/zero-to-jupyterhub-k8s/tree/f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
            [
                MaybeExists(
                    GitHubURL(
                        URL("https://github.com"),
                        URL(
                            "https://github.com/jupyterhub/zero-to-jupyterhub-k8s/tree/f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603"
                        ),
                    )
                ),
                MaybeExists(
                    Git(
                        "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                        "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
                    )
                ),
                MaybeExists(
                    ImmutableGit(
                        "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                        "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
                    )
                ),
            ],
        ),
        (
            "https://github.com/jupyterhub/zero-to-jupyterhub-k8s/tree/0.8.0",
            [
                MaybeExists(
                    GitHubURL(
                        URL("https://github.com"),
                        URL(
                            "https://github.com/jupyterhub/zero-to-jupyterhub-k8s/tree/0.8.0"
                        ),
                    )
                ),
                MaybeExists(
                    Git(
                        "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                        "0.8.0",
                    )
                ),
                Exists(
                    ImmutableGit(
                        "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                        "ada2170a2181ae1760d85eab74e5264d0c6bb67f",
                    )
                ),
            ],
        ),
        # Git URLs that recurse into ImmutableGit
        (
            "git+https://github.com/jupyterhub/zero-to-jupyterhub-k8s@f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
            [
                MaybeExists(
                    Git(
                        "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                        "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
                    )
                ),
                MaybeExists(
                    ImmutableGit(
                        "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                        "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
                    )
                ),
            ],
        ),
        (
            "git+https://github.com/jupyterhub/zero-to-jupyterhub-k8s@0.8.0",
            [
                MaybeExists(
                    Git(
                        "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                        "0.8.0",
                    )
                ),
                Exists(
                    ImmutableGit(
                        "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                        "ada2170a2181ae1760d85eab74e5264d0c6bb67f",
                    )
                ),
            ],
        ),
        (
            "10.5281/zenodo.3232985",
            [
                Exists(Doi(URL("https://zenodo.org/record/3232985"))),
                MaybeExists(
                    ZenodoURL(
                        URL("https://zenodo.org"),
                        URL("https://zenodo.org/record/3232985"),
                    )
                ),
                MaybeExists(ZenodoDataset(URL("https://zenodo.org/"), "3232985")),
            ],
        ),
        (
            "https://doi.org/10.6084/m9.figshare.9782777.v3",
            [
                Exists(
                    Doi(
                        URL(
                            "https://figshare.com/articles/Binder-ready_openSenseMap_Analysis/9782777/3"
                        )
                    )
                ),
                MaybeExists(
                    FigshareURL(
                        FigshareInstallation(
                            URL("https://figshare.com/"),
                            URL("https://api.figshare.com/v2/"),
                        ),
                        URL(
                            "https://figshare.com/articles/Binder-ready_openSenseMap_Analysis/9782777/3"
                        ),
                    )
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
                MaybeExists(
                    ImmutableFigshareDataset(
                        FigshareInstallation(
                            URL("https://figshare.com/"),
                            URL("https://api.figshare.com/v2/"),
                        ),
                        9782777,
                        3,
                    )
                ),
            ],
        ),
        (
            "https://figshare.com/articles/Binder-ready_openSenseMap_Analysis/9782777",
            [
                MaybeExists(
                    FigshareURL(
                        FigshareInstallation(
                            URL("https://figshare.com/"),
                            URL("https://api.figshare.com/v2/"),
                        ),
                        URL(
                            "https://figshare.com/articles/Binder-ready_openSenseMap_Analysis/9782777"
                        ),
                    )
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
            ],
        ),
        # A zenodo doi that uses the /doi redirect
        (
            "https://doi.org/10.5281/zenodo.805993",
            [
                Exists(Doi(url=URL("https://zenodo.org/doi/10.5281/zenodo.805993"))),
                MaybeExists(
                    ZenodoURL(
                        URL("https://zenodo.org"),
                        URL("https://zenodo.org/doi/10.5281/zenodo.805993"),
                    )
                ),
                MaybeExists(ZenodoDataset(URL("https://zenodo.org/"), "14007206")),
            ],
        ),
        # A bare git URL, that we'll have to have guessed
        (
            # Using this as HEAD hasn't changed in 16 years
            "https://git.kernel.org/pub/scm/fs/fat/fatattr/fatattr.git/",
            [
                Exists(
                    repo=Git(
                        "https://git.kernel.org/pub/scm/fs/fat/fatattr/fatattr.git/",
                        ref="HEAD",
                    )
                ),
                Exists(
                    repo=ImmutableGit(
                        "https://git.kernel.org/pub/scm/fs/fat/fatattr/fatattr.git/",
                        "3df926a6a9ad5ea02c9f63157a0588125f046441",
                    )
                ),
            ],
        ),
        # A dataverse URL that does *not* exist in our list of well known dataverse installations
        (
            "https://demo.dataverse.org/dataset.xhtml?persistentId=doi:10.70122/FK2/MBQA9G",
            [
                MaybeExists(
                    DataverseURL(
                        URL("https://demo.dataverse.org"),
                        URL(
                            "https://demo.dataverse.org/dataset.xhtml?persistentId=doi:10.70122/FK2/MBQA9G"
                        ),
                    )
                ),
                Exists(
                    DataverseDataset(
                        URL("https://demo.dataverse.org"), "doi:10.70122/FK2/MBQA9G"
                    )
                ),
            ],
        ),
    ),
)
async def test_recurse(url, expected):
    assert await resolve(URL(url), True) == expected
