# `repoproviders`

A strongly typed library for resolving URLs into various kinds of `repositories`
and fetching them.

## Supported Repositories

| Repository                            | Resolver | Fetcher |
| ------------------------------------- | -------- | ------- |
| GitHub Repos                          | ✅       | ✅      |
| GitHub Refs (Commits, Tags, Branches) | ✅       | ✅      |
| GitHub PRs                            | ✅       | ✅      |
| GitHub Action Artifacts               | ✅       | ✅      |
| Gists                                 | ✅       | ✅      |
| Git Repos                             | ✅       | ✅      |
| GitLab Repos                          | ✅       | ✅      |
| GitLab Refs (Commits, Tags, Branches) | ✅       | ✅      |
| Google Drive Folders (Public)         | ✅       | ✅      |
| DOI                                   | ✅       | N/A     |
| Zenodo Repositories                   | ✅       | ✅      |
| Dataverse Repositories                | ✅       | ✅      |
| Figshare                              | ✅       | ✅      |
| Hydroshare                            | ✅       | ✅      |
| Mercurial                             | ❌       | ❌      |
| CKAN                                  | ❌       | ❌      |
| Software Heritage                     | ❌       | ❌      |
| ZIP files over HTTP                   | ❌       | ❌      |
| Codeberg Refs                         | ❌       | ❌      |
