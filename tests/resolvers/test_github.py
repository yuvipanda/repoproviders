import pytest
from yarl import URL

from repoproviders.resolvers.base import MaybeExists
from repoproviders.resolvers.git import Git, GitHubResolver
from repoproviders.resolvers.urls import GitHubURL


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        # GitHub URLs that are not repos
        (
            GitHubURL(URL("https://github.com"), URL("https://github.com/pyOpenSci")),
            None,
        ),
        (
            GitHubURL(
                URL("https://github.com"),
                URL(
                    "https://github.com/yuvipanda/repoproviders/actions/runs/12552733471/job/34999118812"
                ),
            ),
            None,
        ),
        (
            GitHubURL(
                URL("https://github.com"),
                URL("https://github.com/yuvipanda/repoproviders/settings"),
            ),
            None,
        ),
        (
            GitHubURL(
                URL("https://github.com"),
                URL("https://github.com/jupyter/docker-stacks/pull/2194"),
            ),
            None,
        ),
        # Simple github repo URL
        (
            GitHubURL(
                URL("https://github.com"),
                URL("https://github.com/pyOpenSci/pyos-package-template"),
            ),
            MaybeExists(
                Git("https://github.com/pyOpenSci/pyos-package-template", "HEAD")
            ),
        ),
        # Trailing slash normalized?
        (
            GitHubURL(
                URL("https://github.com"),
                URL("https://github.com/pyOpenSci/pyos-package-template/"),
            ),
            MaybeExists(
                Git("https://github.com/pyOpenSci/pyos-package-template", "HEAD")
            ),
        ),
        # blobs and tree
        (
            GitHubURL(
                URL("https://github.com"),
                URL(
                    "https://github.com/pyOpenSci/pyos-package-template/tree/main/includes/licenses"
                ),
            ),
            MaybeExists(
                Git("https://github.com/pyOpenSci/pyos-package-template", "main")
            ),
        ),
        (
            GitHubURL(
                URL("https://github.com"),
                URL(
                    "https://github.com/pyOpenSci/pyos-package-template/tree/original-cookie/docs"
                ),
            ),
            MaybeExists(
                Git(
                    "https://github.com/pyOpenSci/pyos-package-template",
                    "original-cookie",
                )
            ),
        ),
        (
            GitHubURL(
                URL("https://github.com"),
                URL(
                    "https://github.com/pyOpenSci/pyos-package-template/blob/b912433bfae541972c83529359f4181ef0fe9b67/README.md"
                ),
            ),
            MaybeExists(
                Git(
                    "https://github.com/pyOpenSci/pyos-package-template",
                    ref="b912433bfae541972c83529359f4181ef0fe9b67",
                )
            ),
        ),
        (
            GitHubURL(
                URL("https://github.com"),
                URL("https://github.com/yuvipanda/does-not-exist-e43"),
            ),
            MaybeExists(
                Git(repo="https://github.com/yuvipanda/does-not-exist-e43", ref="HEAD")
            ),
        ),
    ),
)
async def test_github(url, expected):
    gh = GitHubResolver()
    assert await gh.resolve(url) == expected
