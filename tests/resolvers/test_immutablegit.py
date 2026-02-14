from logging import Logger

import pytest

from repoproviders.resolvers.base import DoesNotExist, Exists, MaybeExists
from repoproviders.resolvers.git import Git, ImmutableGit, ImmutableGitResolver


@pytest.mark.parametrize(
    ("question", "expected"),
    (
        # Random URL, not a git repo
        (
            Git("https://example.com/something", "HEAD"),
            DoesNotExist(
                ImmutableGit,
                "Could not access git repository at https://example.com/something",
            ),
        ),
        # Resolve a tag
        (
            Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "0.8.0"),
            Exists(
                ImmutableGit(
                    "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                    "ada2170a2181ae1760d85eab74e5264d0c6bb67f",
                )
            ),
        ),
        # Resolve a commit we know exists, although this isn't verified
        (
            Git(
                "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
            ),
            MaybeExists(
                ImmutableGit(
                    "https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
                    "f7f3ff6d1bf708bdc12e5f10e18b2a90a4795603",
                )
            ),
        ),
        # Repo doesn't exist
        (
            Git(repo="https://github.com/yuvipanda/does-not-exist-e43", ref="HEAD"),
            DoesNotExist(
                ImmutableGit,
                "Could not access git repository at https://github.com/yuvipanda/does-not-exist-e43",
            ),
        ),
        # Ref doesn't exist
        (
            Git(
                "https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "does-not-exist"
            ),
            DoesNotExist(
                ImmutableGit,
                "No ref does-not-exist found in repo https://github.com/jupyterhub/zero-to-jupyterhub-k8s",
            ),
        ),
    ),
)
async def test_immutable_git(question, expected, log):
    ig = ImmutableGitResolver()
    assert await ig.resolve(question, log) == expected


async def test_immutable_git_HEAD(log: Logger):
    """
    Extra test to test resolving HEAD, making sure it's the same as resolving "main".

    This can't be fixtured because HEAD and `mail` will keep mocing
    """
    ig = ImmutableGitResolver()
    assert (
        await ig.resolve(
            Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "HEAD"), log
        )
    ) == (
        await ig.resolve(
            Git("https://github.com/jupyterhub/zero-to-jupyterhub-k8s", "main"), log
        )
    )
