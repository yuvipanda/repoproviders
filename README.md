# repoproviders

|            |                                                                                                                                                                                                                                                                                                                                                                                                                              |
| ---------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Package    | [![Latest PyPI Version](https://img.shields.io/pypi/v/repoproviders.svg)](https://pypi.org/project/repoproviders/) [![Supported Python Versions](https://img.shields.io/pypi/pyversions/repoproviders.svg)](https://pypi.org/project/repoproviders/) [![Documentation](https://readthedocs.org/projects/repoproviders/badge/?version=latest)](https://repoproviders.readthedocs.io/en/latest/?badge=latest)                  |
| Meta       | [![BSD-3-Clause](https://img.shields.io/pypi/l/repoproviders.svg)](LICENSE) [![Code of Conduct](https://img.shields.io/badge/Contributor%20Covenant-v2.0%20adopted-ff69b4.svg)](.github/CODE_OF_CONDUCT.md) [![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/) [![Code Style Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black) |
| Automation |                                                                                                                                                                                                                                                                                                                                                                                                                              |

_Detect, resolve and fetch repositories of content_

## Examples

You can try these out with a `pip install repoproviders`.

````shell
# Resolve a GitHub reference
➜ repoproviders resolve https://github.com/yuvipanda/requirements
Git(repo='https://github.com/yuvipanda/requirements', ref='HEAD')
ImmutableGit(repo='https://github.com/yuvipanda/requirements', ref='5a8737831f74a97bf71a7c4e1500fa0223b13d0d')

# Resolve a GitHub reference to a specific branch based on a URL
➜ repoproviders resolve https://github.com/yuvipanda/requirements/tree/master
Git(repo='https://github.com/yuvipanda/requirements', ref='master')
ImmutableGit(repo='https://github.com/yuvipanda/requirements', ref='5a8737831f74a97bf71a7c4e1500fa0223b13d0d')

# Resolve a DOI
➜ repoproviders resolve 10.1126/science.aar3646
Doi(url='https://www.science.org/doi/10.1126/science.aar3646')

# Resolve a DOI that points to another resolver we support (Dataverse)
➜ repoproviders resolve 10.7910/DVN/6ZXAGT
Doi(url='https://dataverse.harvard.edu/citation?persistentId=doi:10.7910/DVN/6ZXAGT')
DataverseDataset(installationUrl='https://dataverse.harvard.edu', persistentId='doi:10.7910/DVN/6ZXAGT')```

# Resolve a Zenodo DOI
➜ repoproviders resolve 10.5281/zenodo.805993
Doi(url='https://zenodo.org/doi/10.5281/zenodo.805993')
ZenodoDataset(installationUrl='https://zenodo.org/', recordId='14007206')

# Resolve a Zenodo URL directly
➜ repoproviders resolve https://zenodo.org/records/14007206
ZenodoDataset(installationUrl='https://zenodo.org/', recordId='14007206')
````

## Copyright

- Copyright © 2024 Yuvi Panda.
- Free software distributed under the [3-Clause BSD License](./LICENSE).
