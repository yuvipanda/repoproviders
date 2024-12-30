from dataclasses import dataclass


@dataclass
class NotFound:
    """
    Resolver recognizes this question, but while resolving determined it does not exist
    """

    pass
