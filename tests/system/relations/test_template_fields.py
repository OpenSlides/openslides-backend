from tests.system.action.base import BaseActionTestCase

from .setup import (
    FakeModelA,
    FakeModelB,
    FakeModelC,
    assure_model_in_registry,
    assure_model_rm_from_registry,
)


class CreateActionWithTemplateFieldTester(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        for model in (FakeModelA, FakeModelB, FakeModelC):
            assure_model_in_registry(model)

    def tearDown(self) -> None:
        super().tearDown()
        for model in (FakeModelA, FakeModelB, FakeModelC):
            assure_model_rm_from_registry(model)

    def test_simple_create(self) -> None:
        self.create_model("meeting/42")
        self.create_model("fake_model_b/123", {"meeting_id": 42})
        response = self.request(
            "fake_model_a.create", {"fake_model_b_$_ids": {42: [123]}}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_a/1")
        model = self.get_model("fake_model_a/1")
        self.assertEqual(model.get("fake_model_b_$42_ids"), [123])
        self.assertEqual(model.get("fake_model_b_$_ids"), ["42"])
        model = self.get_model("fake_model_b/123")
        self.assertEqual(model.get("structured_relation_field"), 1)

    def test_complex_create(self) -> None:
        self.set_models(
            {
                "meeting/42": {},
                "meeting/43": {},
                "meeting/44": {},
                "fake_model_a/234": {
                    "meeting_id": 42,
                    "fake_model_b_$42_ids": [3451],
                    "fake_model_b_$43_ids": [3452],
                    "fake_model_b_$_ids": ["42", "43"],
                },
                "fake_model_b/3451": {
                    "meeting_id": 42,
                    "structured_relation_field": 234,
                },
                "fake_model_b/3452": {
                    "meeting_id": 43,
                    "structured_relation_field": 234,
                },
                "fake_model_b/3453": {"meeting_id": 44},
            }
        )
        response = self.request(
            "fake_model_a.create", {"fake_model_b_$_ids": {44: [3453]}}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_a/235")
        model = self.get_model("fake_model_a/235")
        self.assertEqual(model.get("fake_model_b_$44_ids"), [3453])
        self.assertEqual(model.get("fake_model_b_$_ids"), ["44"])
        model = self.get_model("fake_model_b/3453")
        self.assertEqual(model.get("structured_relation_field"), 235)

    def test_complex_update_1(self) -> None:
        self.set_models(
            {
                "meeting/42": {},
                "meeting/43": {},
                "meeting/44": {},
                "fake_model_a/234": {
                    "meeting_id": 42,
                    "fake_model_b_$42_ids": [3451],
                    "fake_model_b_$43_ids": [3452],
                    "fake_model_b_$_ids": ["42", "43"],
                },
                "fake_model_b/3451": {
                    "meeting_id": 42,
                    "structured_relation_field": 234,
                },
                "fake_model_b/3452": {
                    "meeting_id": 43,
                    "structured_relation_field": 234,
                },
                "fake_model_b/3453": {"meeting_id": 44},
            }
        )
        response = self.request(
            "fake_model_a.update", {"id": 234, "fake_model_b_$_ids": {44: [3453]}}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_a/234")
        model = self.get_model("fake_model_a/234")
        self.assertEqual(model.get("fake_model_b_$42_ids"), [3451])
        self.assertEqual(model.get("fake_model_b_$43_ids"), [3452])
        self.assertEqual(model.get("fake_model_b_$44_ids"), [3453])
        self.assertEqual(
            set(model.get("fake_model_b_$_ids", [])), set(["42", "43", "44"])
        )
        model = self.get_model("fake_model_b/3453")
        self.assertEqual(model.get("structured_relation_field"), 234)

    def test_complex_update_2(self) -> None:
        self.set_models(
            {
                "meeting/42": {},
                "meeting/43": {},
                "meeting/44": {},
                "fake_model_a/234": {
                    "meeting_id": 42,
                    "fake_model_b_$42_ids": [3451],
                    "fake_model_b_$43_ids": [3452],
                    "fake_model_b_$_ids": ["42", "43"],
                },
                "fake_model_b/3451": {
                    "meeting_id": 42,
                    "structured_relation_field": 234,
                },
                "fake_model_b/3452": {
                    "meeting_id": 43,
                    "structured_relation_field": 234,
                },
                "fake_model_b/3453": {"meeting_id": 43},
            }
        )
        response = self.request(
            "fake_model_a.update", {"id": 234, "fake_model_b_$_ids": {43: [3453]}}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_a/234")
        model = self.get_model("fake_model_a/234")
        self.assertEqual(model.get("fake_model_b_$42_ids"), [3451])
        self.assertEqual(model.get("fake_model_b_$43_ids"), [3453])
        self.assertEqual(set(model.get("fake_model_b_$_ids", [])), set(["42", "43"]))
        model = self.get_model("fake_model_b/3453")
        self.assertEqual(model.get("structured_relation_field"), 234)

    def test_complex_update_3(self) -> None:
        self.set_models(
            {
                "meeting/42": {},
                "meeting/43": {},
                "meeting/44": {},
                "fake_model_a/234": {
                    "meeting_id": 42,
                    "fake_model_b_$42_ids": [3451],
                    "fake_model_b_$43_ids": [3452],
                    "fake_model_b_$_ids": ["42", "43"],
                },
                "fake_model_b/3451": {
                    "meeting_id": 42,
                    "structured_relation_field": 234,
                },
                "fake_model_b/3452": {
                    "meeting_id": 43,
                    "structured_relation_field": 234,
                },
            }
        )
        # empty array behaves the same as None
        response = self.request(
            "fake_model_a.update", {"id": 234, "fake_model_b_$_ids": {43: []}}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_a/234")
        model = self.get_model("fake_model_a/234")
        self.assertEqual(model.get("fake_model_b_$42_ids"), [3451])
        self.assertEqual(model.get("fake_model_b_$43_ids"), None)
        self.assertEqual(model.get("fake_model_b_$_ids"), ["42"])
        model = self.get_model("fake_model_b/3452")
        self.assertEqual(model.get("structured_relation_field"), None)

    def test_complex_update_4(self) -> None:
        self.set_models(
            {
                "meeting/42": {},
                "meeting/43": {},
                "fake_model_a/234": {
                    "fake_model_b_$42_ids": [3451],
                    "fake_model_b_$43_ids": [3452],
                    "fake_model_b_$_ids": ["42", "43"],
                },
                "fake_model_b/3451": {
                    "meeting_id": 42,
                    "structured_relation_field": 234,
                },
                "fake_model_b/3452": {
                    "meeting_id": 43,
                    "structured_relation_field": 234,
                },
            }
        )
        # when setting to None, the replacement IS removed from the template field
        response = self.request(
            "fake_model_a.update", {"id": 234, "fake_model_b_$_ids": {43: None}}
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_a/234")
        model = self.get_model("fake_model_a/234")
        self.assertEqual(model.get("fake_model_b_$42_ids"), [3451])
        self.assertNotIn("fake_model_b_$43_ids", model)
        self.assertEqual(model.get("fake_model_b_$_ids"), ["42"])
        model = self.get_model("fake_model_b/3452")
        self.assertEqual(model.get("structured_relation_field"), None)
