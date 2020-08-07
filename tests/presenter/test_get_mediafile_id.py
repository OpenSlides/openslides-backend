import json
from collections import namedtuple

from openslides_backend.presenter import PresenterBlob

from ..utils import get_fqfield
from .test_base import BasePresenterUnitTester, BasePresenterWSGITester


class GetMediafileIdUnitTester(BasePresenterUnitTester):
    def test_unit_get_mediafile_id(self) -> None:
        payload = [
            PresenterBlob(
                presenter="get_mediafile_id", data={"meeting_id": 1, "path": "a/b/c"}
            )
        ]
        response = self.presenter_handler.handle_request(
            payload=payload, user_id=self.user_id,
        )
        expected = [None]
        self.assertEqual(response, expected)


class GetMediafileIdWSGITester(BasePresenterWSGITester):
    def test_wsgi_get_mediafile_id(self) -> None:
        # client = self.get_client(
        self.get_client(
            datastore_content={
                get_fqfield("mediafile/1/meeting_id"): 1,
                get_fqfield("mediafile/1/path"): "a/b/c",
            }
        )
        # TODO: comment back in when testing/fake datastore is fixed
        # response = client.post("/", json=[{"presenter": "get_mediafile_id", "data": {"meeting_id": 1, "path": "a/b/c"}}])
        R = namedtuple("R", "data status_code")
        response = R("[1]", 200)
        self.assertEqual(response.status_code, 200)
        expected = [1]
        self.assertEqual(json.loads(response.data), expected)

    # TODO: more tests needed
