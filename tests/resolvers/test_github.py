import pytest
from yarl import URL

from repoproviders.resolvers.base import DoesNotExist, Exists, MaybeExists
from repoproviders.resolvers.git import Git, GitHubPRResolver, GitHubResolver
from repoproviders.resolvers.repos import CompressedFile, GitHubPR, GitHubURL


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
            MaybeExists(
                GitHubPR(
                    URL("https://github.com"),
                    URL("https://github.com/jupyter/docker-stacks/pull/2194"),
                )
            ),
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
        (
            GitHubURL(
                URL("https://github.com/jupyter/governance"),
                URL(
                    "https://github.com/jupyter/governance/archive/31ca8204d8ca6366d968de2c10bcf5572f7a048e.zip"
                ),
            ),
            Exists(
                repo=CompressedFile(
                    url=URL(
                        "https://github.com/jupyter/governance/archive/31ca8204d8ca6366d968de2c10bcf5572f7a048e.zip"
                    ),
                    mime_type="application/zip",
                    etag='"bf3c60d9118d8e1317c0852e8b2e3e9b7a9176413f512262b08ddc7a7659d804"',
                )
            ),
        ),
        (
            GitHubURL(
                URL("https://github.com/jupyter/governance"),
                URL(
                    "https://github.com/jupyter/governance/archive/random-words-not-found.zip"
                ),
            ),
            None,
        ),
    ),
)
async def test_github(url, expected):
    gh = GitHubResolver()
    assert await gh.resolve(url) == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        (
            GitHubPR(
                URL("https://github.com"),
                URL("https://github.com/jupyter/docker-stacks/pull/2194"),
            ),
            MaybeExists(
                Git(
                    "https://github.com/mathbunnyru/docker-stacks",
                    "update_oracledb_version",
                )
            ),
        ),
        (
            GitHubPR(
                URL("https://github.com"),
                URL("https://github.com/jupyter/docker-stacks/pull/219400000000"),
            ),
            DoesNotExist(
                GitHubPR,
                "PR 219400000000 does not exist at https://github.com/jupyter/docker-stacks/pull/219400000000",
            ),
        ),
    ),
)
async def test_github_pr(url, expected):
    gh_pr = GitHubPRResolver()
    assert await gh_pr.resolve(url) == expected
