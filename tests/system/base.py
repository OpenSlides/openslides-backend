from typing import Any, Dict
from unittest import TestCase

from openslides_backend.services.datastore.interface import Datastore
from openslides_backend.shared.interfaces import (
    Event,
    WriteRequestElement,
    WSGIApplication,
)
from openslides_backend.shared.patterns import FullQualifiedId
from tests.system.util import Client


class BaseSystemTestCase(TestCase):
    def setUp(self) -> None:
        app = self.get_application()
        self.client = Client(app)
        self.datastore: Datastore = app.services.datastore()  # type: ignore
        self.datastore.truncate_db()

    def get_application(self) -> WSGIApplication:
        raise NotImplementedError()

    def create_model(self, fqid: FullQualifiedId, data: Dict[str, Any]) -> None:
        request = WriteRequestElement(
            events=[Event(type="create", fqid=fqid, fields=data)],
            information={},
            user_id=0,
        )
        self.datastore.write(request)

    def assert_model_exists(self, fqid: FullQualifiedId) -> None:
        model = self.datastore.get(fqid)
        assert model
