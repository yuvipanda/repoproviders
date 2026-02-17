from logging import Logger
from pathlib import Path

import aiohttp
from tenacity import AsyncRetrying, stop_after_delay, wait_fixed, wait_random
from yarl import URL

from repoproviders.resolvers.repos import SWHID

API_BASE_URL = URL("https://archive.softwareheritage.org/api/1")


class SWHIDFetcher:
    async def download_dir(
        self,
        session: aiohttp.ClientSession,
        dir_hash: str,
        output_dir: Path,
        log: Logger,
    ):
        # https://docs.softwareheritage.org/devel/swh-vault/api.html is API reference
        # Trailing slash is absolutely required here
        cook_url = API_BASE_URL / "vault/directory" / (dir_hash + "/")
        # initial_post = await session.post(cook_url)
        # print((await initial_post.json()))

        async for attempt in AsyncRetrying(
            stop=stop_after_delay(600000), wait=wait_fixed(1000) + wait_random(0, 2)
        ):
            with attempt:
                resp = await session.post(cook_url)
                data = await resp.json()

                print(data)
                if data["status"] == "done":
                    print(data)
                    break
                else:
                    raise Exception("Try again")

    async def fetch(self, repo: SWHID, output_dir: Path, log: Logger):
        async with aiohttp.ClientSession() as session:
            match repo.type:
                case "dir":
                    await self.download_dir(session, repo.hash, output_dir, log)
