import asyncio
import re
from dataclasses import dataclass

from yarl import URL

from .base import NotFound


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


class GitHubResolver:
    async def resolve(self, question: URL) -> Git | None:
        # git+<scheme> urls are handled by a different resolver
        if question.scheme not in ("http", "https") or (
            question.host != "github.com" and question.host != "www.github.com"
        ):
            # TODO: Allow configuring for GitHub enterprise
            return None

        # Split the URL into parts, discarding empty parts to account for leading and trailing slashes
        parts = [p for p in question.path.split("/") if p.strip() != ""]
        if len(parts) == 2:
            # Handle <user|org>/<repo>
            # Reconstruct the URL so we normalize any
            return Git(
                repo=str(question.with_path(f"{parts[0]}/{parts[1]}")), ref="HEAD"
            )
        elif len(parts) >= 4 and parts[2] in ("tree", "blob"):
            # Handle <user|org>/<repo>/<tree|blob>/<ref>(/<possible-path>)
            # Note: We ignore any paths specified here, as we only care about the repo
            return Git(
                repo=str(question.with_path(f"{parts[0]}/{parts[1]}")), ref=parts[3]
            )
        else:
            # This is not actually a valid GitHub URL we support
            return None


class ImmutableGitResolver:
    async def resolve(self, question: Git) -> ImmutableGit | NotFound | None:
        command = ["git", "ls-remote", "--", question.repo, question.ref]
        proc = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = [s.decode().strip() for s in await proc.communicate()]
        retcode = await proc.wait()
        if retcode:
            # `git` may follow redirects here, so the repo we pass may not always be the repo we
            # get back. So we loosely check for a 'not found' message.
            if re.search(r"fatal: repository '(.+)' not found", stderr, re.MULTILINE):
                return NotFound()

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
            else:
                return NotFound()
        else:
            resolved_ref = stdout.split("\t", 1)[0]

        return ImmutableGit(question.repo, resolved_ref)


class GitUrlResolver:
    """
    Resolves raw git URLs

    URL structure is inspired by what `pip` supports: https://pip.pypa.io/en/stable/topics/vcs-support/#git
    """

    async def resolve(self, question: URL) -> Git | None:
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

        return Git(str(repo), ref)
