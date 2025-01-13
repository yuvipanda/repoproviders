from dataclasses import dataclass

from yarl import URL


@dataclass(frozen=True)
class GitHubURL:
    """
    A GitHub URL of any sort.

    Not just a repository URL.
    """

    installation: URL
    url: URL

    # URLs can point to whatever
    immutable = False


@dataclass(frozen=True)
class Doi:
    url: URL

    # This needs further investigation
    immutable = False


@dataclass(frozen=True)
class DataverseURL:
    """
    Any kind of URL in any dataverse installation

    Not just for datasets.
    """

    installation: URL
    url: URL

    immutable = False


@dataclass(frozen=True)
class DataverseDataset:
    installationUrl: URL
    persistentId: str

    # Dataverse Datasets also have versions, which are not represented here.
    immutable = False


@dataclass(frozen=True)
class ZenodoURL:
    """
    Any kind of URL in any Zenodo / Invenio installation.

    Not just for records.
    """

    installation: URL
    url: URL

    immutable = False


@dataclass(frozen=True)
class ZenodoDataset:
    installationUrl: URL
    recordId: str

    # Zenodo records are immutable: https://help.zenodo.org/docs/deposit/about-records/#life-cycle
    # When a new version is published, it gets its own record id!
    immutable = True


@dataclass(frozen=True)
class FigshareInstallation:
    url: URL
    apiUrl: URL


@dataclass(frozen=True)
class FigshareURL:
    """
    Any kind of URL in any Figshare installation.

    Not just for articles / datasets.
    """

    installation: FigshareInstallation
    url: URL

    immutable = False


@dataclass(frozen=True)
class FigshareDataset:
    installation: FigshareInstallation
    articleId: int
    version: int | None

    # Figshare articles have versions, and here we don't know if this one does or not
    immutable = False


@dataclass(frozen=True)
class ImmutableFigshareDataset:
    installation: FigshareInstallation
    articleId: int
    # version will always be present when immutable
    version: int

    # We *know* there's a version here
    immutable = True
