from tests.util import get_fqid

from .base import BasePresenterTestCase


class TestGetMediafileId(BasePresenterTestCase):
    def test_simple(self) -> None:
        self.create_model(get_fqid("mediafile/1"), {"meeting_id": 1, "path": "a/b/c"})
        status_code, data = self.request(
            "get_mediafile_id", {"meeting_id": 1, "path": "a/b/c"}
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, 1)

    # TODO: more tests needed
