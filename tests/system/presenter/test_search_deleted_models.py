from typing import Any

from .base import BasePresenterTestCase


class TestSearchDeletedModels(BasePresenterTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.users = {
            i: {
                "id": i,
                "first_name": f"first{i}",
                "last_name": f"last{i}",
                "username": f"user{i}",
            }
            for i in range(2, 6)
        }
        self.motions = {
            i: {
                "id": i,
                "title": f"title{i}",
            }
            for i in range(1, 5)
        }
        self.motions[1]["number"] = "42"
        self.assignments = {
            i: {
                "id": i,
                "title": f"title{i}",
            }
            for i in range(1, 5)
        }
        user_group = {
            "group_$1_ids": [1],
        }
        meeting_id = {
            "meeting_id": 1,
        }
        # add not deleted models
        self.set_models(
            {
                "meeting/1": {
                    "user_ids": [5],
                    "motion_ids": [4],
                    "assignment_ids": [4],
                    "group_ids": [1],
                },
                "group/1": {
                    "meeting_id": 1,
                },
                "user/5": self.users[5] | user_group,
                "motion/4": self.motions[4] | meeting_id,
                "assignment/4": self.assignments[4] | meeting_id,
            }
        )
        # add deleted models
        self.set_models(
            {
                "user/2": self.users[2] | user_group,
                "user/3": self.users[3] | user_group,
                "user/4": self.users[4],
                "motion/1": self.motions[1] | meeting_id,
                "motion/2": self.motions[2] | meeting_id,
                "motion/3": self.motions[3],
                "assignment/1": self.assignments[1] | meeting_id,
                "assignment/2": self.assignments[2] | meeting_id,
                "assignment/3": self.assignments[3],
            },
            True,
        )

    def search_deleted_models(
        self,
        collection: str,
        filter_string: str,
        meeting_id: int = 1,
        status_code: int = 200,
    ) -> Any:
        actual_status_code, data = self.request(
            "search_deleted_models",
            {
                "collection": collection,
                "filter_string": filter_string,
                "meeting_id": meeting_id,
            },
        )
        self.assertEqual(actual_status_code, status_code)
        return data

    def test_search_users_first_name(self) -> None:
        data = self.search_deleted_models("user", "%first2%")
        self.assertCountEqual(data.keys(), ["2"])
        self.assertEqual(data.get("2") | self.users[2], data.get("2"))

    def test_search_users_last_name_multiple_results(self) -> None:
        data = self.search_deleted_models("user", "%user%")
        self.assertCountEqual(data.keys(), ["2", "3"])
        self.assertEqual(data.get("2") | self.users[2], data.get("2"))
        self.assertEqual(data.get("3") | self.users[3], data.get("3"))

    def test_search_users_not_in_meeting(self) -> None:
        data = self.search_deleted_models("user", "%last4%")
        self.assertEqual(data, {})

    def test_search_users_start_of_string_not_found(self) -> None:
        data = self.search_deleted_models("user", "ser%")
        self.assertEqual(data, {})

    def test_search_users_start_of_string_found(self) -> None:
        data = self.search_deleted_models("user", "%ser%")
        self.assertCountEqual(data.keys(), ["2", "3"])
        self.assertEqual(data.get("2") | self.users[2], data.get("2"))
        self.assertEqual(data.get("3") | self.users[3], data.get("3"))

    def test_search_motions_one_result(self) -> None:
        data = self.search_deleted_models("motion", "title1")
        self.assertCountEqual(data.keys(), ["1"])
        self.assertEqual(data.get("1") | self.motions[1], data.get("1"))

    def test_search_motions_multiple_results(self) -> None:
        data = self.search_deleted_models("motion", "title%")
        self.assertCountEqual(data.keys(), ["1", "2"])
        self.assertEqual(data.get("1") | self.motions[1], data.get("1"))
        self.assertEqual(data.get("2") | self.motions[2], data.get("2"))

    def test_search_motions_number(self) -> None:
        data = self.search_deleted_models("motion", "42")
        self.assertCountEqual(data.keys(), ["1"])
        self.assertEqual(data.get("1") | self.motions[1], data.get("1"))

    def test_search_assignments_one_result(self) -> None:
        data = self.search_deleted_models("assignment", "title1")
        self.assertCountEqual(data.keys(), ["1"])
        self.assertEqual(data.get("1") | self.assignments[1], data.get("1"))

    def test_search_assignments_multiple_results(self) -> None:
        data = self.search_deleted_models("assignment", "title%")
        self.assertCountEqual(data.keys(), ["1", "2"])
        self.assertEqual(data.get("1") | self.assignments[1], data.get("1"))
        self.assertEqual(data.get("2") | self.assignments[2], data.get("2"))
