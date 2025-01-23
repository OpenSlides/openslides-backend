import pytest

from openslides_backend.migrations import BadEventException
from openslides_backend.migrations.core.events import to_event


def test_to_event_unknown_event():
    row = {"type": "unknown"}
    with pytest.raises(BadEventException):
        to_event(row)
