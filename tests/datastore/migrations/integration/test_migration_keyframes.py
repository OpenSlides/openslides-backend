from unittest.mock import MagicMock

import pytest

from openslides_backend.datastore.shared.util import BadCodingError
from openslides_backend.migrations import BaseEvent
from openslides_backend.migrations.core.migration_keyframes import (
    DatabaseMigrationKeyframeModifier,
    MigrationKeyframeModifier,
)


def test_bad_event():
    class MyEvent(BaseEvent):
        pass

    modifier = MigrationKeyframeModifier(
        MagicMock(), MagicMock(), MagicMock(), MagicMock()
    )
    modifier._fetch_model = MagicMock()  # type: ignore
    with pytest.raises(BadCodingError):
        modifier.apply_event(MyEvent("a/1", {}))


def test_database_keyframe_modifier_position():
    with pytest.raises(BadCodingError):
        DatabaseMigrationKeyframeModifier(
            MagicMock(), 0, MagicMock(), MagicMock(), MagicMock()
        )


def test_database_keyframe_modifier_non_persistent():
    modifier = DatabaseMigrationKeyframeModifier(
        MagicMock(), 1, MagicMock(), MagicMock(), False
    )
    with pytest.raises(BadCodingError):
        modifier.move_to_next_position()


def test_database_keyframe_modifier_no_keyframe():
    connection = MagicMock()
    connection.query_single_value = MagicMock(return_value=None)
    with pytest.raises(BadCodingError):
        DatabaseMigrationKeyframeModifier(
            connection, 1, MagicMock(), MagicMock(), False
        )
