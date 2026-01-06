import dataclasses
import json
from typing import Any

from yarl import URL

from repoproviders.resolvers.base import DoesNotExist, Exists, MaybeExists

from .base import Repo


class _Encoder(json.JSONEncoder):
    def default(self, o: URL | Any | type) -> str | Any:
        if isinstance(o, URL):
            return str(o)
        elif isinstance(o, type):
            return o.__name__
        else:
            return super().default(o)


def to_json(answer: DoesNotExist[Repo] | Exists[Repo] | MaybeExists[Repo]):
    """
    Convert an answer into a canonical JSON representation
    """
    match answer:
        case DoesNotExist(_, _):
            return json.dumps(
                {
                    "certainity": answer.__class__.__name__,
                    "kind": answer.kind.__name__,
                    "data": dataclasses.asdict(answer),
                },
                cls=_Encoder,
            )
        case Exists(repo) | MaybeExists(repo):
            return json.dumps(
                {
                    "certainity": answer.__class__.__name__,
                    "kind": answer.repo.__class__.__name__,
                    "data": dataclasses.asdict(repo),
                },
                cls=_Encoder,
            )
