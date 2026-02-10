from pathlib import Path
from subprocess import CalledProcessError

from ..resolvers.git import ImmutableGit
from ..utils import exec_process


class ImmutableGitFetcher:
    async def fetch(self, repo: ImmutableGit, output_dir: Path):

        # Assume output_dir is empty
        command = [
            "git",
            "clone",
            "--filter=tree:0",
            "--recurse-submodules",
            repo.repo,
            str(output_dir),
        ]
        retcode, stdout, stderr = await exec_process(command)

        if retcode != 0:
            # FIXME: Raise a more helpful error?
            raise CalledProcessError(retcode, command, stdout, stderr)

        command = ["git", "checkout", repo.ref]

        retcode, stdout, stderr = await exec_process(command, cwd=str(output_dir))

        if retcode != 0:
            # FIXME: Raise a more helpful error?
            raise CalledProcessError(retcode, command, stdout, stderr)
