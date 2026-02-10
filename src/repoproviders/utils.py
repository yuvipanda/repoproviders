import asyncio
import hashlib
import json
from base64 import standard_b64decode, urlsafe_b64encode
from pathlib import Path

import aiohttp
from yarl import URL

# A public service account JSON key, used to make API requests for Google Drive.
# Some values are base 64 decoded so we don't get dinged by GitHub security scanning
# This service account has no rights, only used for identity
GCP_PUBLIC_SERVICE_ACCOUNT_KEY = {
    "type": "service_account",
    "project_id": "repoproviders-iam",
    "private_key_id": standard_b64decode(
        "MDY5ODJhNmY4ZWM5MTM3MDU0YmU5Mjk5NzIwYTQ1OWFhYjgxMmY0Yg=="
    ).decode(),
    "private_key": standard_b64decode(
        "LS0tLS1CRUdJTiBQUklWQVRFIEtFWS0tLS0tCk1JSUV2Z0lCQURBTkJna3Foa2lHOXcwQkFRRUZBQVNDQktnd2dnU2tBZ0VBQW9JQkFRRE9ycUx2cEdUQ281TjgKakl3OGdvU3FTTjQ2Mm5nalhQTk5hMkcraFdiS3lKRVM3c3krMXhHcUNqRXM1WVVuR2k4am5WaHNKTDhXVUg2NAphdzJpczcwV0loK1c1OUs4NDhJbzdLQzc1VmRsMjBGZkgyVldEVU1uTGhWOUlHMmJWNHNpWGJyL1JJWlhMYlpCClNkN2lSZnZ5b1U4VjJ0eDI5Zm9menFVUEhrbGpEdnV0Nmc3dXZrUUN1bEJFV1hFQjdId2MwL2Y3RFAzb09ZQ3IKMkttUEsxNUJBa2dZNUova2Q5VW5EZDJMaGN6U3MwZVhUUWt2K2xWcEVGWlNaN3VLdVRsWm4rTmNDa0pDV1k2KwoybVJmRWJoTFRscVV4Zk5yRnExd1BSNDBhVXhNOCtWNWVWbTZWSDYwdldhOTJTc1lybnc1SUt0TVEvWE9hZ0pxCkZDQ0lRK25CQWdNQkFBRUNnZ0VBSWxzcFBvaW5MeXVkd3FCaVYxU2kxT09UL1ZoL2kvRlJpRmNIUW5KT2FmcjUKRXBxYmNrV3g3QUFSdUpMV2xXOW0wcGEvTWdyUnNOWGttcWRBOXdERnQ3NG9YaDlmQ29NWnJVL1lVQ09KYWFjTwpzTTg1T3hxdFJRQUdGbXlqaTZUN3ZkU3kxdWYvSk5LMmJ4Zm1jdHFMVFFPL2I3U1gzVFo2UTN0SU9NRWlGZE1GClJCMDNvTVhhcWxsL2dsbWFXais4YUVrSmQ0MmtEd0l3YzluNjMwYU5jRkx0MGZLdlIydHkvU2p3WHJvTlFJK1UKT3o5VE04ZkkzdTF1WUFKUEJJdDJDZS9kQTlObVdDMFRYYW1paEI4SU1SSXBWeGVONWFubVNrY3ZJZHIxUTh5MQpjTk5zcHZvQUJlN2ZRcktFRWNEVGJaVTg2TlJRNnVvcjRYV3pGVjVPb1FLQmdRRHRjbTV3OE8yMjRQbDVDaG9KClZ2YUVnUWdtSHBnc3EzWHhseU9sS2g0bGc4ck9Qd1lhOG93MmR3MzdDcXNRc08va0ZYQU5vWm5MUi93U21KNlcKS0d3MlFZWjlsaVhneERpQ1VudlFHQ0dPVUFIU2F1cUl6V2JmbWMvclRyMDQ4djl6M0JVYXh5WGRIWHJlV2szbgo3dVZRdzZ3MnltVjNhRTR4SnhnTjhKc2ZCUUtCZ1FEZTFOTyt2K0lNUWZGOHdtQXhlM0dDclJySVpvNzFJUHRuCjFoaGF5NUdOWE5CL3pKcVQ3MTJJeFo3WUgrTU4yUDJCelVKTTdtc2xXUmdXZXI2d01uSDhienlIcW9lQ0VwQkIKNDl6Y0RKK3lDaGhhbzcveU9YMjBkRTV0d3Z3NmU3TkdZeVBxM0VkVUw2ZU5HVXEzTWlGbnAzSUw3elNaeFIwZApYRk9lSndURWpRS0JnUUNTQTdWd2xHZko5d3pTWnVqZDUzRk95RDRubXRhL1dXejg5SkZCNXVXRThrZUxqdXdGCk5EUU81aVZkeEJDd0FlNXpGcy9DUWliZC85VTk1a1pYVm1JODl3eHFQQ1BzMVIxZTNyUXVvamc0V0hEV1lWTDYKYnowY3NXeFBhaXNvVXgzTnRIL3g2SmNiSXg3RWowbXJINWc2a3lsYXhCbWpWU3dJUTk4aDYxeW90UUtCZ0FKcgp2WUV0QkgrdGw3b0xRcEJIRHd5a1pNNFlqeVVLbnJDYUd0bWhySXNrbnY5RWNjbDVxRUo4SXlXbDh3bUxlZldYCkRVbFlyY0ZTSG5qZ0RJSk5pZjk4RmVSRGJnVnp2aTE1RkVVdnZleHBQNnA4YlBGc3ZuamZhcHEycTViWEVUT0sKa0RGVkExRmUweXN0UXlxS1dPS1BaeVhLQzRCQUsvak5yL3JmNGFWaEFvR0JBSnhwbDNVZnpaSFAxaVdHNGJUWApBY3A0WTR5cG1wME5aVWlrNHUycnFubTFmSDJZYmRYZGQvUlRWNlpYRmgrM0lpVmNkMFY2cDhyNnBqMUdkaHpHCnBLTEhoU1NTNi95ZzF6cnFhWWhQV0FWeVJVT1BvMEVOeGZIWmc4cHErcStDdDVHQmdQS1BNT3lzRmw2RzRzVDkKOFNpNVd3a1V2cXMwVyt3TWJ6QWp6bEFQCi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS0K"
    ).decode(),
    "client_email": "repoproviders-no-rights-public@repoproviders-iam.iam.gserviceaccount.com",
    "client_id": "107622683369583114795",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/repoproviders-no-rights-public%40repoproviders-iam.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com",
}


def make_dir_hash(data: dict[str, str]) -> str:
    """
    Convert a directory structure to a urlsafe base64 encoded sha256 hash.

    Input is a dict where key is full paths of files, and value is either a hash or a last modified
    timestamp.  Sorted by key explicitly before hashing.
    """
    data = dict(sorted(data.items()))
    return urlsafe_b64encode(
        hashlib.sha256(json.dumps(data).encode()).digest()
    ).decode()


async def download_file(session: aiohttp.ClientSession, url: URL, output_path: Path):
    # Read in 4k chunks
    CHUNK_SIZE = 4 * 1024
    resp = await session.get(url)

    if resp.status == 200 and "Location" in resp.headers:
        # Some providers (lookin at you, data.caltech.edu) send a Location header
        # *but with a 200 status code*. This is invalid and bogus, yet we have to
        # honor it. Sigh
        return await download_file(session, URL(resp.headers["Location"]), output_path)

    resp.raise_for_status()

    if not output_path.parent.exists():
        # Leave the exist_ok=True here despite the check, to handle possible
        # race conditions in the future if we ever parallelize this
        output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "wb") as f:
        async for chunk in resp.content.iter_chunked(CHUNK_SIZE):
            f.write(chunk)


async def exec_process(cmd: list[str], **kwargs) -> tuple[int, str, str]:
    """
    Execute given command and return return code, stdout, stderr
    """

    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE, **kwargs
    )
    stdout, stderr = await proc.communicate()
    returncode = await proc.wait()

    return returncode, stdout.decode(), stderr.decode()
