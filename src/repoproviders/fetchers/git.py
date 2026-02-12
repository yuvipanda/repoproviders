from pathlib import Path
from subprocess import CalledProcessError
from tempfile import NamedTemporaryFile
from zipfile import ZipFile

import aiohttp
from yarl import URL

from repoproviders.resolvers.repos import GitHubActionArtifact

from ..resolvers.git import ImmutableGit
from ..utils import GITHUB_PUBLIC_PAT, download_file, exec_process


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


class GitHubActionArtifactFetcher:
    async def fetch(self, repo: GitHubActionArtifact, output_dir: Path):
        # Assume this standard archive URL holds
        # If this starts to fail, we shall make an additional GitHub API request
        # to this URL: https://docs.github.com/en/rest/actions/artifacts?apiVersion=2022-11-28#get-an-artifact
        # FIXME: Support other installations
        download_url = (
            URL("https://api.github.com/repos/")
            / repo.account
            / repo.repo
            / "actions/artifacts"
            / str(repo.artifact_id)
            / "zip"
        )

        async with aiohttp.ClientSession(
            headers={"Authorization": f"Bearer {GITHUB_PUBLIC_PAT}"}
        ) as session:
            with NamedTemporaryFile() as temp_file:
                await download_file(session, download_url, Path(temp_file.name))
                compressed_file = ZipFile(temp_file.name)
                compressed_file.extractall(output_dir)
