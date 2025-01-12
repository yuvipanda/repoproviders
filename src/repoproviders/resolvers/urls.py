from dataclasses import dataclass

from yarl import URL


@dataclass(frozen=True)
class GitHubURL:
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
