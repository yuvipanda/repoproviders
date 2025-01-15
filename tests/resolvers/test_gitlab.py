import pytest
from yarl import URL

from repoproviders.resolvers.base import MaybeExists
from repoproviders.resolvers.git import Git, GitLabResolver
from repoproviders.resolvers.repos import GitLabURL


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        # GitLab URLs that are not repos
        (
            GitLabURL(URL("https://gitlab.com"), URL("https://gitlab.com/mosaik/")),
            None,
        ),
        (
            GitLabURL(
                URL("https://gitlab.com"),
                URL("https://gitlab.com/groups/mosaik/-/packages"),
            ),
            None,
        ),
        (
            GitLabURL(
                URL("https://gitlab.com"),
                # Put a - at the end to test for edge cases
                URL("https://gitlab.com/groups/mosaik/something/something/-"),
            ),
            None,
        ),
        (
            GitLabURL(
                URL("https://gitlab.com"),
                URL("https://gitlab.com/mosaik/mosaik/-/merge_requests/194"),
            ),
            None,
        ),
        # Simple GitLab repo URL
        (
            GitLabURL(
                URL("https://gitlab.com"), URL("https://gitlab.com/mosaik/mosaik")
            ),
            MaybeExists(Git("https://gitlab.com/mosaik/mosaik", "HEAD")),
        ),
        # blobs and tree
        (
            GitLabURL(
                URL("https://gitlab.com"),
                URL(
                    "https://gitlab.com/mosaik/examples/mosaik-tutorials-on-binder/-/blob/b2c44e7f804dc1634681540582b1731e0393f69b/03_Same_Time_Loop/_01_controller_master.ipynb?ref_type=heads"
                ),
            ),
            MaybeExists(
                Git(
                    "https://gitlab.com/mosaik/examples/mosaik-tutorials-on-binder",
                    "b2c44e7f804dc1634681540582b1731e0393f69b",
                )
            ),
        ),
        (
            GitLabURL(
                URL("https://gitlab.com"),
                URL(
                    "https://gitlab.com/mosaik/examples/mosaik-tutorials-on-binder/-/tree/b2c44e7f804dc1634681540582b1731e0393f69b/03_Same_Time_Loop?ref_type=heads"
                ),
            ),
            MaybeExists(
                Git(
                    "https://gitlab.com/mosaik/examples/mosaik-tutorials-on-binder",
                    "b2c44e7f804dc1634681540582b1731e0393f69b",
                )
            ),
        ),
        (
            GitLabURL(
                URL("https://gitlab.wikimedia.org"),
                URL(
                    "https://gitlab.wikimedia.org/toolforge-repos/toolviews/-/tree/main/toolviews?ref_type=heads"
                ),
            ),
            MaybeExists(
                Git("https://gitlab.wikimedia.org/toolforge-repos/toolviews", "main")
            ),
        ),
        (
            GitLabURL(
                URL("https://gitlab.wikimedia.org"),
                URL(
                    "https://gitlab.wikimedia.org/toolforge-repos/toolviews/-/blob/main/toolviews/__init__.py?ref_type=heads"
                ),
            ),
            MaybeExists(
                Git("https://gitlab.wikimedia.org/toolforge-repos/toolviews", "main")
            ),
        ),
        (
            GitLabURL(
                URL("https://gitlab.com"),
                URL(
                    "https://gitlab.com/mosaik/examples/mosaik-tutorials-on-binder/-/tree/b2c44e7f804dc1634681540582b1731e0393f69b/03_Same_Time_Loop?ref_type=heads"
                ),
            ),
            MaybeExists(
                Git(
                    "https://gitlab.com/mosaik/examples/mosaik-tutorials-on-binder",
                    "b2c44e7f804dc1634681540582b1731e0393f69b",
                )
            ),
        ),
        (
            GitLabURL(
                URL("https://gitlab.com"),
                URL("https://gitlab.com/yuvipanda/does-not-exist-e43"),
            ),
            MaybeExists(
                Git(repo="https://gitlab.com/yuvipanda/does-not-exist-e43", ref="HEAD")
            ),
        ),
        # Non repo URLs should simply be detected to be not a repo
        (
            GitLabURL(
                URL("https://gitlab.wikimedia.org"),
                URL(
                    "https://gitlab.wikimedia.org/toolforge-repos/toolviews/-/merge_requests/11"
                ),
            ),
            None,
        ),
    ),
)
async def test_gitlab(url, expected):
    gl = GitLabResolver()
    assert await gl.resolve(url) == expected
