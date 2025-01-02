import asyncio
import secrets
import socket
import sys
import tempfile
from pathlib import Path

import aiohttp
from yarl import URL

from repoproviders.utils import download_file


def random_port() -> int:
    """
    Get a single random port that is *probably* unused
    """
    sock = socket.socket()
    sock.bind(("", 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


async def test_download_file():
    port = random_port()
    with tempfile.TemporaryDirectory() as src, tempfile.TemporaryDirectory() as dest:
        test_file = Path(src) / secrets.token_hex(8)
        test_contents = secrets.token_hex(8)
        proc = await asyncio.create_subprocess_exec(
            sys.executable, "-m", "http.server", str(port), "-d", src, "-b", "127.0.0.1"
        )
        try:
            # FIXME: Do this a little more dynamically?
            # Wait for the HTTP server to come up
            await asyncio.sleep(1)

            test_file.write_text(test_contents)

            # Create a nested subdirectory
            dest_file = Path(dest) / secrets.token_hex(8) / secrets.token_hex(8)
            async with aiohttp.ClientSession() as session:
                await download_file(
                    session, URL(f"http://127.0.0.1:{port}/{test_file.name}"), dest_file
                )

            assert dest_file.exists()
            assert dest_file.read_text() == test_contents
        finally:
            proc.kill()
            await proc.wait()
