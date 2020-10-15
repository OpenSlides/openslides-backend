from werkzeug.test import Client as WerkzeugClient
from werkzeug.wrappers import BaseResponse

from openslides_backend.shared.interfaces import WSGIApplication
from openslides_backend.shared.patterns import (
    KEYSEPARATOR,
    Collection,
    FullQualifiedField,
    FullQualifiedId,
)


class Client(WerkzeugClient):
    def __init__(self, application: WSGIApplication):
        super().__init__(application, BaseResponse)


def get_fqid(value: str) -> FullQualifiedId:
    """
    Returns a FullQualifiedId parsed from the given value.
    """
    collection, id = value.split(KEYSEPARATOR)
    return FullQualifiedId(Collection(collection), int(id))


def get_fqfield(value: str) -> FullQualifiedField:
    """
    Returns a FullQualifiedField parsed from the given value.
    """
    collection, id, field = value.split(KEYSEPARATOR)
    return FullQualifiedField(Collection(collection), int(id), field)


def get_id_from_fqid(fqid: str) -> int:
    id = fqid.split(KEYSEPARATOR)[1]
    return int(id)
