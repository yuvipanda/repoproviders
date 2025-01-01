from pathlib import Path
from typing import Any, Protocol


class SupportsFetch(Protocol):
    async def fetch(self, repo: Any, output_dir: Path):
        pass
