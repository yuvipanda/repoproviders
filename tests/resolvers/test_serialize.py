import json

import pytest

from repoproviders import resolve
from repoproviders.resolvers.serialize import to_json


@pytest.mark.parametrize(
    ("url", "expected"),
    (
        ("https://example.com", None),
        (
            "https://github.com/pyOpenSci",
            {
                "certainity": "MaybeExists",
                "kind": "GitHubURL",
                "data": {
                    "installation": "https://github.com",
                    "url": "https://github.com/pyOpenSci",
                },
            },
        ),
        (
            "https://github.com/pyOpenSci/pyos-package-template/tree/main/includes/licenses",
            {
                "certainity": "Exists",
                "kind": "ImmutableGit",
                "data": {
                    "repo": "https://github.com/pyOpenSci/pyos-package-template",
                    "ref": "c77ad6399f713ee3a021ef52b069e56b17de24a7",
                },
            },
        ),
        (
            "doi:10.7910/DVN/6ZXAGT/3YRRYJ",
            {
                "certainity": "Exists",
                "kind": "DataverseDataset",
                "data": {
                    "installationUrl": "https://dataverse.harvard.edu",
                    "persistentId": "doi:10.7910/DVN/6ZXAGT",
                },
            },
        ),
        (
            "https://figshare.com/articles/Binder-ready_openSenseMap_Analysis/9782777",
            {
                "certainity": "Exists",
                "kind": "ImmutableFigshareDataset",
                "data": {
                    "installation": {
                        "url": "https://figshare.com/",
                        "apiUrl": "https://api.figshare.com/v2/",
                    },
                    "articleId": 9782777,
                    "version": 3,
                },
            },
        ),
        (
            "https://github.com/yuvipanda/does-not-exist-e43",
            {
                "certainity": "DoesNotExist",
                "kind": "ImmutableGit",
                "data": {
                    "kind": "ImmutableGit",
                    "message": "Could not access git repository at https://github.com/yuvipanda/does-not-exist-e43",
                },
            },
        ),
    ),
)
async def test_to_json(url, expected, log):
    # This also tests to_dict anyway
    answers = await resolve(url, True, log)
    if expected is None:
        assert answers == []
    else:
        assert answers is not None
        assert to_json(answers[-1]) == json.dumps(expected)
