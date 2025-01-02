import asyncio
from pathlib import Path
from subprocess import CalledProcessError

from ..resolvers.git import ImmutableGit


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
        proc = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = [s.decode().strip() for s in await proc.communicate()]
        retcode = await proc.wait()

        if retcode != 0:
            # FIXME: Raise a more helpful error?
            raise CalledProcessError(retcode, command, stdout, stderr)

        command = ["git", "checkout", repo.ref]

        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(output_dir)
        )

        stdout, stderr = [s.decode().strip() for s in await proc.communicate()]
        retcode = await proc.wait()

        if retcode != 0:
            # FIXME: Raise a more helpful error?
            raise CalledProcessError(retcode, command, stdout, stderr)
