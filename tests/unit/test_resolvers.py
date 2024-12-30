import pytest
from repoproviders import resolvers
from repoproviders.resolvers import Git, Doi, ImmutableGit, NotFound
from yarl import URL

@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://example.com/something", None),
        # GitHub URLs that are not repos
        ("https://github.com/pyOpenSci", None),
        ("https://github.com/yuvipanda/repoproviders/actions/runs/12552733471/job/34999118812", None),
        ("https://github.com/yuvipanda/repoproviders/settings", None),
        ("https://github.com/jupyter/docker-stacks/pull/2194", None),
        # Simple github repo URL
        ("https://github.com/pyOpenSci/pyos-package-template", Git("https://github.com/pyOpenSci/pyos-package-template", "HEAD")),
        # Trailing slash normalized?
        ("https://github.com/pyOpenSci/pyos-package-template/", Git("https://github.com/pyOpenSci/pyos-package-template", "HEAD")),
        # blobs and tree
        ("https://github.com/pyOpenSci/pyos-package-template/tree/main/includes/licenses", Git("https://github.com/pyOpenSci/pyos-package-template", "main")),
        ("https://github.com/pyOpenSci/pyos-package-template/tree/original-cookie/docs", Git("https://github.com/pyOpenSci/pyos-package-template", "original-cookie")),
        ("https://github.com/pyOpenSci/pyos-package-template/blob/b912433bfae541972c83529359f4181ef0fe9b67/README.md", Git("https://github.com/pyOpenSci/pyos-package-template", ref="b912433bfae541972c83529359f4181ef0fe9b67"))
    )
)
async def test_github(url, expected):
    gh = resolvers.GitHubResolver()
    assert await gh.resolve(URL(url)) == expected

@pytest.mark.parametrize(
    ("question", "expected"),
    (
        # Random URL, not a git repo
        (Git("https://example.com/something", "HEAD"), NotFound()),
        # Resolve a tag
        (Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "0.8.0"), ImmutableGit("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "ada2170a2181ae1760d85eab74e5264d0c6bb67f")),
        # Resolve a commit we know exists, although this isn't verified
        (Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603"), ImmutableGit("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603")),
        (Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "does-not-exist"), NotFound()),
    )
)
async def test_immutable_git(question, expected):
    ig = resolvers.ImmutableGitResolver()
    assert await ig.resolve(question) == expected

async def test_immutable_git_HEAD():
    """
    Extra test to test resolving HEAD, making sure it's the same as resolving "main".

    This can't be fixtured because HEAD and `mail` will keep mocing
    """
    ig = resolvers.ImmutableGitResolver()
    assert (await ig.resolve(Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "main"))) == (await ig.resolve(Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "main")))


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://example.com/something", None),
        # doi schema'd URI
        ("doi:10.7910/DVN/6ZXAGT/3YRRYJ", Doi("https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ")),
        # handle schema'd URI
        ("hdl:11529/10016", Doi("https://data.cimmyt.org/dataset.xhtml?persistentId=hdl:11529/10016")),
        # For convenience, we do accept DOIs without a scheme
        ("10.7910/DVN/6ZXAGT/3YRRYJ", Doi("https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ")),
        # But not handles without a scheme
        ("11529/10016", None),
        # Three DOI resolution URLs
        ("https://doi.org/10.7910/DVN/6ZXAGT/3YRRYJ", Doi("https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ")),
        ("https://www.doi.org/10.7910/DVN/6ZXAGT/3YRRYJ", Doi("https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ")),
        ("https://hdl.handle.net/10.7910/DVN/6ZXAGT/3YRRYJ", Doi("https://dataverse.harvard.edu/file.xhtml?persistentId=doi:10.7910/DVN/6ZXAGT/3YRRYJ")),
    )
)
async def test_doi(url, expected):
    doi = resolvers.DoiResolver()
    assert await doi.resolve(URL(url)) == expected