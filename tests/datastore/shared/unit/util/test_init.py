from unittest.mock import MagicMock

from openslides_backend.datastore.shared.util import (
    DeletedModelsBehaviour,
    ModelDoesNotExist,
    ModelNotDeleted,
    get_exception_for_deleted_models_behaviour,
)


def test_raise_exception_for_deleted_models_behaviour_all_models():
    exception = get_exception_for_deleted_models_behaviour(
        MagicMock(), DeletedModelsBehaviour.ALL_MODELS
    )
    assert type(exception) is ModelDoesNotExist


def test_raise_exception_for_deleted_models_behaviour_no_deleted():
    exception = get_exception_for_deleted_models_behaviour(
        MagicMock(), DeletedModelsBehaviour.NO_DELETED
    )
    assert type(exception) is ModelDoesNotExist


def test_raise_exception_for_deleted_models_behaviour_only_deleted():
    exception = get_exception_for_deleted_models_behaviour(
        MagicMock(), DeletedModelsBehaviour.ONLY_DELETED
    )
    assert type(exception) is ModelNotDeleted
