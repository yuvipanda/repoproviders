import re

from aiohttp import ClientSession
from yarl import URL

from repoproviders.utils import exec_process

from .base import DoesNotExist, Exists, MaybeExists
from .repos import (
    GistURL,
    Git,
    GitHubActionArtifact,
    GitHubPR,
    GitHubURL,
    GitLabURL,
    ImmutableGit,
)


class GitHubResolver:
    async def resolve(
        self, question: GitHubURL
    ) -> (
        MaybeExists[Git]
        | MaybeExists[GitHubPR]
        | MaybeExists[GitHubActionArtifact]
        | None
    ):
        url = question.url
        # Split the URL into parts, discarding empty parts to account for leading and trailing slashes
        parts = [p for p in url.path.split("/") if p.strip() != ""]
        if len(parts) == 2:
            # Handle <user|org>/<repo>
            # Reconstruct the URL so we normalize any
            return MaybeExists(
                Git(repo=str(url.with_path(f"{parts[0]}/{parts[1]}")), ref="HEAD")
            )
        elif len(parts) >= 4 and parts[2] in ("tree", "blob"):
            # Handle <user|org>/<repo>/<tree|blob>/<ref>(/<possible-path>)
            # Note: We ignore any paths specified here, as we only care about the repo
            return MaybeExists(
                Git(repo=str(url.with_path(f"{parts[0]}/{parts[1]}")), ref=parts[3])
            )
        elif len(parts) == 4 and parts[2] == "pull" and parts[3].isdigit():
            # Resolve pull requests to the branch their head ref points to
            return MaybeExists(GitHubPR(question.installation, question.url))
        elif len(parts) == 7 and parts[5] == "artifacts" and parts[6].isdigit():
            # An artifact uploaded by GitHub actions. We don't know if this is still unexpired
            return MaybeExists(
                GitHubActionArtifact(
                    question.installation, parts[0], parts[1], int(parts[6])
                )
            )
        else:
            # This is not actually a valid GitHub URL we support
            return None


class GitHubPRResolver:
    async def resolve(
        self, question: GitHubPR
    ) -> MaybeExists[Git] | DoesNotExist[GitHubPR] | None:
        parts = [p for p in question.url.path.split("/") if p.strip() != ""]
        org = parts[0]
        repo = parts[1]
        pull_req_id = int(parts[3])
        async with ClientSession() as session:
            # FIXME: Support enterprise github installations
            # FIXME: Add authentication support
            api_url = (
                URL("https://api.github.com/repos")
                / org
                / repo
                / "pulls"
                / str(pull_req_id)
            )
            resp = await session.get(api_url)

            data = await resp.json()
            if resp.status == 404:
                return DoesNotExist(
                    GitHubPR, f"PR {pull_req_id} does not exist at {question.url}"
                )
            repo_url = data["head"]["repo"]["html_url"]
            ref = data["head"]["ref"]
            return MaybeExists(Git(repo_url, ref))


class GistResolver:
    async def resolve(self, question: GistURL) -> MaybeExists[Git] | None:
        url = question.url
        # Split the URL into parts, discarding empty parts to account for leading and trailing slashes
        parts = [p for p in url.path.split("/") if p.strip() != ""]

        if len(parts) == 2:
            # Handle user/gist-id
            return MaybeExists[Git](repo=Git(str(question.url), "HEAD"))

        # FIXME: Handle ways to specify individual refs in Gist.
        # I can't seem to find a
        return None


class GitLabResolver:
    async def resolve(self, question: GitLabURL) -> MaybeExists[Git] | None:
        url = question.url
        # Split the URL into parts, discarding empty parts to account for leading and trailing slashes
        parts = [p for p in url.path.split("/") if p.strip() != ""]
        if len(parts) in (2, 3):
            # Handle <user|org>/<repo> as well as <user|org>/<namespace>/<repo>
            # Reconstruct the URL so we normalize any
            return MaybeExists(
                # Clear out the URL to remove query params & fragments
                Git(repo=str(url.with_query(None).with_fragment(None)), ref="HEAD")
            )
        elif "-" in parts:
            dash_index = parts.index("-")
            if len(parts) == dash_index + 1:
                # The dash is the last part of the URL, which isn't something we recognize to be anything
                return None
            if not parts[dash_index + 1] in ("tree", "blob"):
                # GitLab has dashes in lots of URLs, we only care about tree and blob ones
                return None
            return MaybeExists(
                Git(
                    str(url.with_path("/".join(parts[0:dash_index]))),
                    parts[dash_index + 2],
                )
            )
        else:
            # This is not actually a valid GitLab URL we support
            return None


class ImmutableGitResolver:
    async def resolve(
        self, question: Git
    ) -> (
        Exists[ImmutableGit]
        | MaybeExists[ImmutableGit]
        | DoesNotExist[ImmutableGit]
        | None
    ):
        command = ["git", "ls-remote", "--", question.repo, question.ref]
        retcode, stdout, stderr = await exec_process(command)

        if retcode:
            # `git` may follow redirects here, so the repo we pass may not always be the repo we
            # get back. So we loosely check for a 'not found' message.
            if re.search(r"fatal: repository '(.+)' not found", stderr, re.MULTILINE):
                return DoesNotExist(
                    ImmutableGit, f"Could not access git repository at {question.repo}"
                )

            # If it's another error, let's raise it directly
            raise RuntimeError(
                f"Unable to run git ls-remote to resolve {question}: {stderr}"
            )

        if stdout == "":
            # The remote repo exists, and we can talk to it. But no *ref* with the given name
            # exists. We check if this looks like a commit sha, and if it is, assume it exists.
            # FIXME: Decide if we just do this check *before* trying ls-remotes? Faster, but it means
            # we can't guarantee that the repo itself exists
            if re.match(r"[0-9a-f]{40}", question.ref):
                resolved_ref = question.ref
                return MaybeExists(ImmutableGit(question.repo, resolved_ref))
            else:
                return DoesNotExist(
                    ImmutableGit, f"No ref {question.ref} found in repo {question.repo}"
                )
        else:
            resolved_ref = stdout.split("\t", 1)[0]

            return Exists(ImmutableGit(question.repo, resolved_ref))


class GitUrlResolver:
    """
    Resolves raw git URLs

    URL structure is inspired by what `pip` supports: https://pip.pypa.io/en/stable/topics/vcs-support/#git
    """

    async def resolve(self, question: URL) -> MaybeExists[Git] | None:
        # List of supported protocols is from https://pip.pypa.io/en/stable/topics/vcs-support/#git
        if question.scheme not in (
            "git+https",
            "git+ssh",
            "git",
            "git+file",
            "git+http",
            "git+git",
        ):
            return None

        repo = question.with_scheme(question.scheme.replace("git+", ""))

        if "@" in question.path:
            parts = question.path.split("@", 1)
            ref = parts[1]
            repo = repo.with_path(parts[0])
        else:
            ref = "HEAD"

        return MaybeExists(Git(str(repo), ref))
