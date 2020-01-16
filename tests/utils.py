from werkzeug.test import Client as WerkzeugClient
from werkzeug.wrappers import BaseResponse

from openslides_backend.shared.patterns import Collection, FullQualifiedField


class ResponseWrapper(BaseResponse):
    pass


class Client(WerkzeugClient):
    pass


def get_fqfield(key: str) -> FullQualifiedField:
    collection, id, field = key.split("/")
    return FullQualifiedField(Collection(collection), int(id), field)
