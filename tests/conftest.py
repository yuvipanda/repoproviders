import logging

import pytest


@pytest.fixture()
def log() -> logging.Logger:
    return logging.getLogger()
