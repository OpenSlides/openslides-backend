from .base import BasePresenterTestCase


class TestGetUsers(BasePresenterTestCase):
    def test_temporary_filter_pagenation(self) -> None:
        self.create_model("meeting/1", {"name": "meeting1"})
        self.create_model(
            "user/2",
            {"username": "florian", "first_name": "Florian", "last_name": "Freiheit"},
        )
        self.create_model(
            "user/3", {"username": "test", "first_name": "Testy", "last_name": "Tester"}
        )
        self.create_model(
            "user/4",
            {
                "username": "john",
                "first_name": "John",
                "last_name": "Xylon",
                "meeting_id": 1,
            },
        )
        status_code, data = self.request(
            "get_users",
            {
                "start_index": 1,
                "entries": 2,
                "sort_criteria": ["username"],
                "reverse": False,
                "include_temporary": False,
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"users": [2, 3]})

    def test_keywords_filter(self) -> None:
        self.create_model("meeting/1", {"name": "meeting1"})
        self.create_model(
            "user/2",
            {"username": "florian", "first_name": "Florian", "last_name": "Freiheit"},
        )
        self.create_model(
            "user/3", {"username": "test", "first_name": "Testy", "last_name": "Tester"}
        )
        self.create_model(
            "user/4",
            {
                "username": "john",
                "first_name": "John",
                "last_name": "Xylon",
                "meeting_id": 1,
            },
        )
        self.create_model(
            "user/5", {"username": "xorr", "first_name": "John", "last_name": "Xorr"}
        )
        status_code, data = self.request(
            "get_users",
            {
                "start_index": 0,
                "entries": 100,
                "sort_criteria": ["first_name", "username"],
                "reverse": True,
                "include_temporary": True,
                "filter": "John",
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"users": [5, 4]})

    def test_keywords_pagenated(self) -> None:
        self.create_model("meeting/1", {"name": "meeting1"})
        self.create_model(
            "user/2",
            {"username": "florian", "first_name": "Florian", "last_name": "Freiheit"},
        )
        self.create_model(
            "user/3", {"username": "test", "first_name": "Testy", "last_name": "Tester"}
        )
        self.create_model(
            "user/4",
            {
                "username": "john",
                "first_name": "John",
                "last_name": "Xylon",
                "meeting_id": 1,
            },
        )
        self.create_model(
            "user/5", {"username": "xorr", "first_name": "John", "last_name": "Xorr"}
        )
        status_code, data = self.request(
            "get_users",
            {
                "start_index": 1,
                "entries": 1,
                "sort_criteria": ["first_name", "username"],
                "reverse": True,
                "include_temporary": True,
                "filter": "John",
            },
        )
        self.assertEqual(status_code, 200)
        self.assertEqual(data, {"users": [4]})
