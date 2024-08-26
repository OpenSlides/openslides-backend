from openslides_backend.permissions.permissions import Permissions
from openslides_backend.shared.util import ONE_ORGANIZATION_FQID
from tests.system.action.base import BaseActionTestCase


class AssignmentCreateActionTest(BaseActionTestCase):
    def test_create(self) -> None:
        self.create_model(
            "meeting/110",
            {
                "name": "name_zvfbAjpZ",
                "agenda_item_creation": "always",
                "list_of_speakers_initially_closed": True,
                "is_active_in_organization_id": 1,
            },
        )
        response = self.request(
            "assignment.create", {"title": "test_Xcdfgee", "meeting_id": 110}
        )
        self.assert_status_code(response, 200)
        assert response.json["results"] == [[{"id": 1, "sequential_number": 1}]]
        model = self.get_model("assignment/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 110
        assert model.get("open_posts") == 0
        assert model.get("phase") == "search"
        assert model.get("sequential_number") == 1
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 110)
        self.assertEqual(agenda_item.get("content_object_id"), "assignment/1")
        self.assert_model_exists(
            "list_of_speakers/1", {"content_object_id": "assignment/1", "closed": True}
        )

    def test_create_other_agenda_item_check(self) -> None:
        self.create_model(
            "meeting/110",
            {
                "name": "name_zvfbAjpZ",
                "agenda_item_creation": "default_yes",
                "is_active_in_organization_id": 1,
            },
        )
        response = self.request(
            "assignment.create", {"title": "test_Xcdfgee", "meeting_id": 110}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 110
        agenda_item = self.get_model("agenda_item/1")
        self.assertEqual(agenda_item.get("meeting_id"), 110)
        self.assertEqual(agenda_item.get("content_object_id"), "assignment/1")

    def test_create_other_agenda_item_check_2(self) -> None:
        self.create_model(
            "meeting/110",
            {
                "name": "name_zvfbAjpZ",
                "agenda_item_creation": "default_no",
                "is_active_in_organization_id": 1,
            },
        )
        response = self.request(
            "assignment.create", {"title": "test_Xcdfgee", "meeting_id": 110}
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 110
        self.assert_model_not_exists("agenda_item/1")

    def test_create_other_agenda_item_check_3(self) -> None:
        self.create_model(
            "meeting/110",
            {
                "name": "name_zvfbAjpZ",
                "agenda_item_creation": "never",
                "is_active_in_organization_id": 1,
            },
        )
        response = self.request(
            "assignment.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 110,
                "agenda_create": True,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 110
        self.assert_model_not_exists("agenda_item/1")

    def test_create_agenda_item_no_default(self) -> None:
        self.create_model(
            "meeting/110",
            {"agenda_item_creation": "default_no", "is_active_in_organization_id": 1},
        )
        response = self.request(
            "assignment.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 110,
                "agenda_create": True,
            },
        )
        self.assert_status_code(response, 200)
        model = self.get_model("assignment/1")
        assert model.get("title") == "test_Xcdfgee"
        assert model.get("meeting_id") == 110
        agenda_item = self.get_model("agenda_item/1")
        assert agenda_item.get("content_object_id") == "assignment/1"

    def test_create_full_fields(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_zvfbAjpZ",
                    "agenda_item_creation": "default_yes",
                    "is_active_in_organization_id": 1,
                    "meeting_mediafile_ids": [11],
                },
                "mediafile/1": {
                    "owner_id": "meeting/110",
                    "meeting_mediafile_ids": [11],
                },
                "meeting_mediafile/11": {"mediafile_id": 1, "meeting_id": 110},
            }
        )
        response = self.request(
            "assignment.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 110,
                "description": "text_test1",
                "open_posts": 12,
                "phase": "search",
                "default_poll_description": "text_test2",
                "number_poll_candidates": True,
                "attachment_ids": [1],
            },
        )
        self.assert_status_code(response, 200)
        self.assert_model_exists(
            "assignment/1",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 110,
                "description": "text_test1",
                "open_posts": 12,
                "phase": "search",
                "default_poll_description": "text_test2",
                "number_poll_candidates": True,
                "attachment_ids": [11],
                "sequential_number": 1,
            },
        )
        self.assert_model_exists(
            "agenda_item/1", {"meeting_id": 110, "content_object_id": "assignment/1"}
        )

    def test_create_non_published_orga_attachments(self) -> None:
        self.set_models(
            {
                "meeting/110": {
                    "name": "name_zvfbAjpZ",
                    "agenda_item_creation": "default_yes",
                    "is_active_in_organization_id": 1,
                    "admin_group_id": 1,
                },
                "mediafile/1": {
                    "owner_id": ONE_ORGANIZATION_FQID,
                },
                "group/1": {"admin_group_for_meeting_id": 1},
            }
        )
        response = self.request(
            "assignment.create",
            {
                "title": "test_Xcdfgee",
                "meeting_id": 110,
                "description": "text_test1",
                "open_posts": 12,
                "phase": "search",
                "default_poll_description": "text_test2",
                "number_poll_candidates": True,
                "attachment_ids": [1],
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "Mediafile is neither a meeting mediafile nor published.",
            response.json["message"],
        )

    def test_create_empty_data(self) -> None:
        response = self.request("assignment.create", {})
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must contain ['meeting_id', 'title'] properties",
            response.json["message"],
        )

    def test_create_wrong_field(self) -> None:
        self.create_model(
            "meeting/110", {"name": "name_zvfbAjpZ", "is_active_in_organization_id": 1}
        )
        response = self.request(
            "assignment.create",
            {
                "title": "title_Xcdfgee",
                "meeting_id": 110,
                "wrong_field": "text_AefohteiF8",
            },
        )
        self.assert_status_code(response, 400)
        self.assertIn(
            "data must not contain {'wrong_field'} properties",
            response.json["message"],
        )

    def test_create_no_permission(self) -> None:
        self.base_permission_test(
            {},
            "assignment.create",
            {
                "title": "title_Xcdfgee",
                "meeting_id": 1,
            },
        )

    def test_create_permission(self) -> None:
        self.base_permission_test(
            {},
            "assignment.create",
            {
                "title": "title_Xcdfgee",
                "meeting_id": 1,
            },
            Permissions.Assignment.CAN_MANAGE,
        )

    def test_create_permission_locked_meeting(self) -> None:
        self.base_locked_out_superadmin_permission_test(
            {},
            "assignment.create",
            {
                "title": "title_Xcdfgee",
                "meeting_id": 1,
            },
        )
