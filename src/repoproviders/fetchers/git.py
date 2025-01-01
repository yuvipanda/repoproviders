import asyncio
from pathlib import Path

from ..resolvers.git import ImmutableGit


class ImmutableGitFetcher:
    async def fetch(self, repo: ImmutableGit, output_dir: Path):
        # FIXME: This isn't the most optimized clone but that's ok

        # output_dir should be empty
        command = ["git", "clone", "--recurse-submodules", repo.repo, str(output_dir)]
        proc = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = [s.decode().strip() for s in await proc.communicate()]
        retcode = await proc.wait()

        return
