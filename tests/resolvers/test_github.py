import pytest
from yarl import URL

from repoproviders.resolvers.git import Git, GitHubResolver


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
