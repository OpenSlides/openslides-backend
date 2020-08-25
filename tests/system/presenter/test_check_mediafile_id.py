from tests.util import get_fqid

from .base import BasePresenterTestCase


class TestCheckMediafileId(BasePresenterTestCase):
    def test_simple(self) -> None:
        self.create_model(
            get_fqid("mediafile/1"), {"filename": "the filename", "is_directory": False}
        )
        status_code, data = self.request("check_mediafile_id", {"mediafile_id": 1})
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"ok": True, "filename": "the filename"})

    # TODO: more tests needed
