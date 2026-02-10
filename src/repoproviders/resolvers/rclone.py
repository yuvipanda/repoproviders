from dataclasses import dataclass


@dataclass(frozen=True)
class GoogleDriveItem:
    id: str

    immutable = False
