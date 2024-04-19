from enum import Enum

from .exceptions import DatastoreException, ModelDoesNotExist, ModelNotDeleted


class DeletedModelsBehaviour(int, Enum):
    NO_DELETED = 1
    ONLY_DELETED = 2
    ALL_MODELS = 3


def get_exception_for_deleted_models_behaviour(
    fqid: str, get_deleted_models: DeletedModelsBehaviour
) -> DatastoreException:
    if get_deleted_models == DeletedModelsBehaviour.ONLY_DELETED:
        return ModelNotDeleted(fqid)
    else:
        return ModelDoesNotExist(fqid)
