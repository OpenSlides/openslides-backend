from tests.system.action.base import BaseActionTestCase


class MotionCreateActionTest(BaseActionTestCase):
    def test_create_good_case_required_fields(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_workflow/12",
            {"name": "name_workflow1", "first_state_id": 34, "state_ids": [34]},
        )
        self.create_model(
            "motion_state/34", {"name": "name_state34", "meeting_id": 222}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 222,
                            "workflow_id": 12,
                            "agenda_create": True,
                            "text": "test",
                            "reason": "test",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 222)
        self.assertEqual(agenda_item.get("content_object_id"), "motion/1")

    def test_create_simple_fields(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_workflow/12",
            {"name": "name_workflow1", "first_state_id": 34, "state_ids": [34]},
        )
        self.create_model(
            "motion_state/34", {"name": "name_state34", "meeting_id": 222}
        )
        self.create_model(
            "motion/1",
            {"title": "title_eJveLQIh", "sort_child_ids": [], "meeting_id": 222},
        )
        self.create_model(
            "motion_category/124", {"name": "name_wbtlHQro", "meeting_id": 222}
        )
        self.create_model(
            "motion_block/78", {"title": "title_kXTvKvjc", "meeting_id": 222}
        )
        self.create_model("user/47", {"username": "username_47", "meeting_id": 222})
        self.create_model("tag/56", {"name": "name_56", "meeting_id": 222})
        self.create_model("mediafile/8", {"name": "name_8", "meeting_id": 222})

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 222,
                            "workflow_id": 12,
                            "number": "001",
                            "state_extension": "test_EhbkOWqd",
                            "sort_parent_id": 1,
                            "category_id": 124,
                            "block_id": 78,
                            "supporter_ids": [47],
                            "tag_ids": [56],
                            "attachment_ids": [8],
                            "text": "test",
                            "reason": "test",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/2")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("number") == "001"
        assert model.get("state_extension") == "test_EhbkOWqd"
        assert model.get("sort_parent_id") == 1
        assert model.get("category_id") == 124
        assert model.get("block_id") == 78
        assert model.get("supporter_ids") == [47]
        assert model.get("tag_ids") == [56]
        assert model.get("attachment_ids") == [8]

    def test_create_empty_data(self) -> None:
        response = self.client.post(
            "/", json=[{"action": "motion.create", "data": [{}]}],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must contain [\\'meeting_id\\', \\'title\\'] properties",
            str(response.data),
        )

    def test_create_wrong_field(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "title_test1",
                            "meeting_id": 222,
                            "wrong_field": "text_AefohteiF8",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data[0] must not contain {\\'wrong_field\\'} properties",
            str(response.data),
        )

    def test_create_workflow_id(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_workflow/12",
            {"name": "name_workflow1", "first_state_id": 34, "state_ids": [34]},
        )
        self.create_model(
            "motion_state/34", {"name": "name_state34", "meeting_id": 222}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "title_test1",
                            "meeting_id": 222,
                            "workflow_id": 12,
                            "text": "test",
                            "reason": "test",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        motion = self.get_model("motion/1")
        assert motion.get("state_id") == 34

    def test_create_workflow_id_from_meeting(self) -> None:
        self.create_model(
            "meeting/222", {"name": "name_SNLGsvIV", "motions_default_workflow_id": 13}
        )
        self.create_model(
            "motion_state/35", {"name": "name_PXiCjXaK", "meeting_id": 222}
        )
        self.create_model(
            "motion_workflow/13",
            {"name": "name_workflow1", "first_state_id": 35, "state_ids": [35]},
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "title_test1",
                            "meeting_id": 222,
                            "text": "test",
                            "reason": "test",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        motion = self.get_model("motion/1")
        assert motion.get("state_id") == 35

    def test_create_missing_state(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [{"title": "test_Xcdfgee", "meeting_id": 222}],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Cannot calculate state_id." in str(response.data)

    def test_correct_origin_id_set(self) -> None:
        self.create_model("meeting/221", {"name": "name_XDAddEAW", "committee_id": 53})
        self.create_model(
            "meeting/222",
            {
                "name": "name_SNLGsvIV",
                "motions_default_workflow_id": 12,
                "committee_id": 52,
            },
        )
        self.create_model(
            "motion_workflow/12",
            {"name": "name_workflow1", "first_state_id": 34, "state_ids": [34]},
        )
        self.create_model(
            "motion_state/34", {"name": "name_state34", "meeting_id": 222}
        )
        self.create_model(
            "motion/12", {"title": "title_FcnPUXJB", "meeting_id": 221, "state_id": 34}
        )
        self.create_model("committee/52", {"name": "name_EeKbwxpa"})
        self.create_model(
            "committee/53", {"name": "name_auSwgfJC", "forward_to_committee_ids": [52]}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 222,
                            "origin_id": 12,
                            "text": "test",
                            "reason": "test",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/13")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("origin_id") == 12

    def test_correct_origin_id_wrong_1(self) -> None:
        self.create_model("meeting/221", {"name": "name_XDAddEAW", "committee_id": 53})
        self.create_model(
            "meeting/222",
            {
                "name": "name_SNLGsvIV",
                "motions_default_workflow_id": 12,
                "committee_id": 52,
            },
        )
        self.create_model(
            "motion_workflow/12",
            {"name": "name_workflow1", "first_state_id": 34, "state_ids": [34]},
        )
        self.create_model(
            "motion_state/34", {"name": "name_state34", "meeting_id": 222}
        )
        self.create_model(
            "motion/12", {"title": "title_FcnPUXJB", "meeting_id": 221, "state_id": 34}
        )
        self.create_model("committee/52", {"name": "name_EeKbwxpa"})
        self.create_model(
            "committee/53", {"name": "name_auSwgfJC", "forward_to_committee_ids": []}
        )
        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {"title": "test_Xcdfgee", "meeting_id": 222, "origin_id": 12}
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Committee id 52 not in []" in str(response.data)

    def test_create_good_special_fields_1(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_workflow/12",
            {"name": "name_workflow1", "first_state_id": 34, "state_ids": [34]},
        )
        self.create_model(
            "motion_state/34", {"name": "name_state34", "meeting_id": 222}
        )
        self.create_model(
            "motion/1",
            {"title": "title_eJveLQIh", "sort_child_ids": [], "meeting_id": 222},
        )

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 222,
                            "workflow_id": 12,
                            "lead_motion_id": 1,
                            "text": "text_test1",
                            "reason": "reason_test1",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/2")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("lead_motion_id") == 1
        assert model.get("text") == "text_test1"
        assert model.get("reason") == "reason_test1"

    def test_create_good_special_fields_2(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_workflow/12",
            {"name": "name_workflow1", "first_state_id": 34, "state_ids": [34]},
        )
        self.create_model(
            "motion_state/34", {"name": "name_state34", "meeting_id": 222}
        )
        self.create_model(
            "motion_statute_paragraph/1",
            {"title": "title_eJveLQIh", "meeting_id": 222},
        )

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 222,
                            "workflow_id": 12,
                            "statute_paragraph_id": 1,
                            "reason": "reason_test2",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("statute_paragraph_id") == 1
        assert model.get("reason") == "reason_test2"

    def test_create_good_special_fields_missing_1(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_workflow/12",
            {"name": "name_workflow1", "first_state_id": 34, "state_ids": [34]},
        )
        self.create_model(
            "motion_state/34", {"name": "name_state34", "meeting_id": 222}
        )
        self.create_model(
            "motion/1", {"title": "title_eJveLQIh", "meeting_id": 222},
        )

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 222,
                            "workflow_id": 12,
                            "lead_motion_id": 1,
                            "text": "text_kXTvKvjc",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "reason is required in this context." in str(response.data)

    def test_create_good_special_fields_missing_2(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_workflow/12",
            {"name": "name_workflow1", "first_state_id": 34, "state_ids": [34]},
        )
        self.create_model(
            "motion_state/34", {"name": "name_state34", "meeting_id": 222}
        )
        self.create_model(
            "motion/1", {"title": "title_eJveLQIh", "meeting_id": 222},
        )

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 222,
                            "workflow_id": 12,
                            "lead_motion_id": 1,
                            "reason": "resaon_kXTvKvjc",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "Text or amendment_paragraph is required in this context." in str(
            response.data
        )

    def test_create_good_special_fields_missing_3(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        self.create_model(
            "motion_workflow/12",
            {"name": "name_workflow1", "first_state_id": 34, "state_ids": [34]},
        )
        self.create_model(
            "motion_state/34", {"name": "name_state34", "meeting_id": 222}
        )
        self.create_model(
            "motion/1", {"title": "title_eJveLQIh", "meeting_id": 222},
        )

        response = self.client.post(
            "/",
            json=[
                {
                    "action": "motion.create",
                    "data": [
                        {
                            "title": "test_Xcdfgee",
                            "meeting_id": 222,
                            "workflow_id": 12,
                            "reason": "reason_kXTvKvjc",
                        }
                    ],
                }
            ],
        )
        self.assert_status_code(response, 400)
        assert "text is required in this context." in str(response.data)
