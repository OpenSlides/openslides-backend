from .setup import BaseRelationsTestCase, FakeModelA, FakeModelB, FakeModelC  # noqa


class CreateActionWithTemplateFieldTester(BaseRelationsTestCase):
    def test_simple_create(self) -> None:
        self.create_model("fake_model_b/123", {})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "fake_model_a.create",
                    "data": [{"fake_model_b_$_ids": {42: [123]}}],
                }
            ],
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
                "fake_model_b/3453": {"meeting_id": 44},
            }
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "fake_model_a.create",
                    "data": [{"fake_model_b_$_ids": {44: [3453]}}],
                }
            ],
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
                "fake_model_b/3453": {"meeting_id": 44},
            }
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "fake_model_a.update",
                    "data": [{"id": 234, "fake_model_b_$_ids": {44: [3453]}}],
                }
            ],
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
                "fake_model_b/3453": {"meeting_id": 43},
            }
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "fake_model_a.update",
                    "data": [{"id": 234, "fake_model_b_$_ids": {43: [3453]}}],
                }
            ],
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
        # when setting to empty array, the replacement is not removed from the template field
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "fake_model_a.update",
                    "data": [{"id": 234, "fake_model_b_$_ids": {43: []}}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_a/234")
        model = self.get_model("fake_model_a/234")
        self.assertEqual(model.get("fake_model_b_$42_ids"), [3451])
        self.assertEqual(model.get("fake_model_b_$43_ids"), [])
        self.assertEqual(model.get("fake_model_b_$_ids"), ["42", "43"])
        model = self.get_model("fake_model_b/3452")
        self.assertEqual(model.get("structured_relation_field"), None)

    def test_complex_update_4(self) -> None:
        self.create_model(
            "fake_model_a/234",
            {
                "fake_model_b_$42_ids": [3451],
                "fake_model_b_$43_ids": [3452],
                "fake_model_b_$_ids": ["42", "43"],
            },
        )
        self.create_model(
            "fake_model_b/3451", {"meeting_id": 42, "structured_relation_field": 234}
        )
        self.create_model(
            "fake_model_b/3452", {"meeting_id": 43, "structured_relation_field": 234}
        )
        # when setting to None, the replacement IS removed from the template field
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "fake_model_a.update",
                    "data": [{"id": 234, "fake_model_b_$_ids": {43: None}}],
                }
            ],
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists("fake_model_a/234")
        model = self.get_model("fake_model_a/234")
        self.assertEqual(model.get("fake_model_b_$42_ids"), [3451])
        self.assertNotIn("fake_model_b_$43_ids", model)
        self.assertEqual(model.get("fake_model_b_$_ids"), ["42"])
        model = self.get_model("fake_model_b/3452")
        self.assertEqual(model.get("structured_relation_field"), None)
