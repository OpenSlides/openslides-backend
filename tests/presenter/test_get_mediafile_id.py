import json
from unittest.mock import MagicMock, patch

from openslides_backend.presenter import PresenterBlob

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
        # TODO: move mocking to base class
        datastore = self.client.application.services.datastore()
        retrieve = MagicMock(return_value={"1": {}})
        with patch.object(datastore, "retrieve", retrieve):
            response = self.client.post(
                "/",
                json=[
                    {
                        "presenter": "get_mediafile_id",
                        "data": {"meeting_id": 1, "path": "a/b/c"},
                    }
                ],
            )
            self.assertEqual(response.status_code, 200)
            expected = [1]
            self.assertEqual(json.loads(response.data), expected)

            retrieve.assert_called()
            command = retrieve.call_args[0][0]
            assert command.name == "filter"
            data = command.get_raw_data()
            assert data["collection"] == "mediafile"
            assert len(data["filter"]["and_filter"]) == 2

    # TODO: more tests needed
