from openslides_backend.permissions.permissions import Permissions
from tests.system.action.base import BaseActionTestCase


class MotionCreateActionTest(BaseActionTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.permission_test_model = {
            "motion_workflow/12": {
                "name": "name_workflow1",
                "first_state_id": 34,
                "state_ids": [34],
            },
            "motion_state/34": {"name": "name_state34", "meeting_id": 1},
        }

    def test_create_good_case_required_fields(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_SNLGsvIV"},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {"name": "name_state34", "meeting_id": 222},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "agenda_create": True,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 222
        assert model.get("created") is not None
        assert model.get("created") == model.get("last_modified")
        assert model.get("submitter_ids") == [1]
        submitter = self.get_model("motion_submitter/1")
        assert submitter.get("user_id") == 1
        assert submitter.get("meeting_id") == 222
        assert submitter.get("motion_id") == 1
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 222)
        self.assertEqual(agenda_item.get("content_object_id"), "motion/1")

    def test_create_simple_fields(self) -> None:
        self.create_meeting()
        self.set_user_groups(1, [1])
        self.set_models(
            {
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {"name": "name_state34", "meeting_id": 1},
                "motion/1": {
                    "title": "title_eJveLQIh",
                    "sort_child_ids": [],
                    "meeting_id": 1,
                },
                "motion_category/124": {"name": "name_wbtlHQro", "meeting_id": 1},
                "motion_block/78": {"title": "title_kXTvKvjc", "meeting_id": 1},
                "tag/56": {"name": "name_56", "meeting_id": 1},
                "mediafile/8": {"meeting_id": 1},
            }
        )

        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 12,
                "number": "001",
                "state_extension": "test_EhbkOWqd",
                "sort_parent_id": 1,
                "category_id": 124,
                "block_id": 78,
                "supporter_ids": [1],
                "tag_ids": [56],
                "attachment_ids": [8],
                "text": "test",
                "reason": "test",
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("motion/2")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 1
        assert model.get("number") == "001"
        assert model.get("state_extension") == "test_EhbkOWqd"
        assert model.get("sort_parent_id") == 1
        assert model.get("category_id") == 124
        assert model.get("block_id") == 78
        assert model.get("supporter_ids") == [1]
        assert model.get("tag_ids") == [56]
        assert model.get("attachment_ids") == [8]

    def test_create_empty_data(self) -> None:
        response = self.request("motion.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'title'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        response = self.request(
            "motion.create",
            {
                "title": "title_test1",
                "meeting_id": 222,
                "wrong_field": "text_AefohteiF8",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_workflow_id(self) -> None:
        self.set_models(
            {
                "meeting/222": {"name": "name_SNLGsvIV"},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {"name": "name_state34", "meeting_id": 222},
                "user/1": {"meeting_ids": [222]},
            }
        )
        response = self.request(
            "motion.create",
            {
                "title": "title_test1",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)
        motion = self.get_model("motion/1")
        assert motion.get("state_id") == 34

    def test_create_workflow_id_from_meeting(self) -> None:
        self.set_models(
            {
                "meeting/222": {
                    "name": "name_SNLGsvIV",
                    "motions_default_workflow_id": 13,
                },
                "motion_state/35": {"name": "name_PXiCjXaK", "meeting_id": 222},
                "motion_workflow/13": {
                    "name": "name_workflow1",
                    "first_state_id": 35,
                    "state_ids": [35],
                },
            }
        )
        response = self.request(
            "motion.create", {"title": "title_test1", "meeting_id": 222, "text": "test"}
        )
        self.assert_status_code(response, 200)
        motion = self.get_model("motion/1")
        assert motion.get("state_id") == 35

    def test_create_missing_state(self) -> None:
        self.create_model("meeting/222", {"name": "name_SNLGsvIV"})
        response = self.request(
            "motion.create",
            {"title": "test_Xcdfgee", "meeting_id": 222, "text": "text"},
        )
        self.assert_status_code(response, 400)
        assert "No matching default workflow defined on this meeting" in str(
            response.json["message"]
        )

    def test_create_missing_text(self) -> None:
        self.create_model("meeting/222")
        response = self.request(
            "motion.create", {"title": "test_Xcdfgee", "meeting_id": 222}
        )
        self.assert_status_code(response, 400)
        assert "Text is required" in response.json["message"]

    def test_create_with_amendment_paragraphs(self) -> None:
        self.create_model("meeting/222")
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "text": "text",
                "amendment_paragraph_$": {4: "text"},
            },
        )
        self.assert_status_code(response, 400)
        assert "give amendment_paragraph_$ in this context" in response.json["message"]

    def test_create_reason_missing(self) -> None:
        self.create_model("meeting/222", {"motions_reason_required": True})
        response = self.request(
            "motion.create",
            {"title": "test_Xcdfgee", "meeting_id": 222, "text": "text"},
        )
        self.assert_status_code(response, 400)
        assert "Reason is required" in response.json["message"]

    def test_create_lead_motion_and_statute_paragraph_id_given(self) -> None:
        self.set_models(
            {"meeting/222": {}, "motion_statute_paragraph/1": {"meeting_id": 222}}
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "text": "text",
                "lead_motion_id": 1,
                "statute_paragraph_id": 1,
            },
        )
        self.assert_status_code(response, 400)
        assert "both of lead_motion_id and statute_paragraph_id." in response.json.get(
            "message", ""
        )

    def test_create_with_submitters(self) -> None:
        self.set_models(
            {
                "meeting/222": {},
                "motion_workflow/12": {
                    "name": "name_workflow1",
                    "first_state_id": 34,
                    "state_ids": [34],
                },
                "motion_state/34": {"name": "name_state34", "meeting_id": 222},
            }
        )
        self.set_models(
            {"user/56": {"meeting_ids": [222]}, "user/57": {"meeting_ids": [222]}}
        )
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 222,
                "workflow_id": 12,
                "text": "text",
                "submitter_ids": [56, 57],
            },
        )
        self.assert_status_code(response, 200)
        motion = self.get_model("motion/1")
        assert motion.get("submitter_ids") == [1, 2]
        submitter_1 = self.get_model("motion_submitter/1")
        assert submitter_1.get("meeting_id") == 222
        assert submitter_1.get("user_id") == 56
        assert submitter_1.get("motion_id") == 1
        submitter_2 = self.get_model("motion_submitter/2")
        assert submitter_2.get("meeting_id") == 222
        assert submitter_2.get("user_id") == 57
        assert submitter_2.get("motion_id") == 1

    def test_create_missing_origin_id(self) -> None:
        self.set_models(self.permission_test_model)
        self.create_meeting()
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 12,
                "text": "test",
                "origin_id": 12,
            },
        )
        self.assert_status_code(response, 400)
        assert (
            "data must not contain {'origin_id'} properties" in response.json["message"]
        )

    def test_create_no_permission(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 12,
                "text": "test",
            },
        )

    def test_create_permission_simple_fields(self) -> None:
        self.base_permission_test(
            self.permission_test_model,
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 12,
                "text": "test",
            },
            Permissions.Motion.CAN_CREATE,
        )

    def test_create_permission_missing_can_manage(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_CREATE])
        self.set_models(self.permission_test_model)
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "number": "X13",
                "meeting_id": 1,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 403)
        assert "Forbidden fields: number" in response.json["message"]

    def test_create_permission_with_can_manage(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(
            3, [Permissions.Motion.CAN_CREATE, Permissions.Motion.CAN_MANAGE]
        )
        self.set_models(self.permission_test_model)
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "number": "X13",
                "meeting_id": 1,
                "workflow_id": 12,
                "text": "test",
            },
        )
        self.assert_status_code(response, 200)

    def test_create_no_permission_lead_motion(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(3, [Permissions.Motion.CAN_CREATE])
        self.set_models(self.permission_test_model)
        self.set_models({"motion/3": {"meeting_id": 1}})
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 12,
                "text": "test",
                "lead_motion_id": 3,
            },
        )
        self.assert_status_code(response, 403)
        assert (
            "Missing permission: motion.can_create_amendments"
            in response.json["message"]
        )

    def test_create_permission_lead_motion(self) -> None:
        self.create_meeting()
        self.user_id = self.create_user("user")
        self.login(self.user_id)
        self.set_user_groups(self.user_id, [3])
        self.set_group_permissions(
            3, [Permissions.Motion.CAN_CREATE, Permissions.Motion.CAN_CREATE_AMENDMENTS]
        )
        self.set_models(self.permission_test_model)
        self.set_models({"motion/3": {"meeting_id": 1}})
        response = self.request(
            "motion.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 1,
                "workflow_id": 12,
                "text": "test",
                "lead_motion_id": 3,
            },
        )
        self.assert_status_code(response, 200)
