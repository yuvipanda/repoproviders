from dataclasses import dataclass

from yarl import URL


@dataclass(frozen=True)
class Git:
    repo: str
    ref: str

    immutable = False


@dataclass(frozen=True)
class ImmutableGit:
    """
    Same as Git, but marked to be fully resolved. This implies:

    1. The repository exists, and can be contacted
    2. If ref was a branch or tag, it has been resolved into an immutable commit sha
    3. If ref *looks* like a sha, we assume it exists (without testing it)
    """

    repo: str
    ref: str

    immutable = True


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
class GitHubPR:
    """
    A GitHub Pull Request
    """

    installation: URL
    url: URL

    # PRs can change to whatever
    immutable = False


@dataclass(frozen=True)
class GitHubActionArtifact:
    """
    A downloadable GitHub Action Artifact
    """

    installation: URL
    account: str
    repo: str
    artifact_id: int

    # Artifacts don't change after upload
    immutable = True


@dataclass(frozen=True)
class GistURL:
    """
    A Gist URL of any sort.

    Not just cloneable repo URL
    """

    installation: URL
    url: URL

    # URL can point to whatever
    immutable = False


@dataclass(frozen=True)
class GitLabURL:
    """
    A GitLab URL of any sort.

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


@dataclass(frozen=True)
class HydroshareDataset:
    resource_id: str

    # Hydroshare Datasets are mutable
    immutable = False


@dataclass(frozen=True)
class CKANDataset:
    installationUrl: URL
    dataset_id: str

    immutable = False
