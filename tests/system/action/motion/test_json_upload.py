from typing import Any, Dict, List, TypedDict

from typing_extensions import NotRequired

from openslides_backend.action.mixins.import_mixins import ImportState
from tests.system.action.base import BaseActionTestCase

SetupAmendmentSetting = TypedDict(
    "SetupAmendmentSetting",
    {"fields": List[str], "has_number": NotRequired[bool]},
)

SetupMotionSetting = TypedDict(
    "SetupMotionSetting",
    {
        "amendments": NotRequired[Dict[int, SetupAmendmentSetting]],
        "has_number": NotRequired[bool],
    },
)

SetupWorkflowSetting = TypedDict(
    "SetupWorkflowSetting",
    {"first_state_fields": List[str]},
)

SetupMeetingSetting = TypedDict(
    "SetupMeetingSetting",
    {
        "fields": List[str],
        "motions": NotRequired[Dict[int, SetupMotionSetting]],
        "workflow": NotRequired[SetupWorkflowSetting],
    },
)


class MotionJsonUpload(BaseActionTestCase):
    def build_base_model_data_from_prototype(
        self, prototype: Dict[str, Any], fields: List[str]
    ) -> Dict[str, Any]:
        data = {}
        for field in fields:
            if prototype.get(field):
                data[field] = prototype[field]
        return data

    def set_up_models(self, meetings: Dict[int, SetupMeetingSetting]) -> None:
        workflow_id = 1
        state_id = 1
        model_data = {}
        meeting_prototype = {
            "name": "test",
            "is_active_in_organization_id": 1,
            "motions_reason_required": True,
        }
        first_state_prototype = {"set_number": True}
        amendment_prototype = {
            "amendment_paragraphs": {"1": "one"},
            "text": "<p>I am an amendment 2</p>",
        }
        for meeting_id in meetings:
            motion_number_value = 1
            amendment_number_value = 1
            setting = meetings[meeting_id]
            meeting_data = {
                **self.build_base_model_data_from_prototype(
                    meeting_prototype, setting["fields"]
                ),
                "motions_default_workflow_id": workflow_id,
                "name": "test meeting" + str(meeting_id),
            }
            model_data["motion_workflow/" + str(workflow_id)] = {
                "default_workflow_meeting_id": meeting_id,
                "state_ids": [state_id, state_id + 1, state_id + 2],
                "first_state_id": state_id,
            }
            if workflow := setting.get("workflow"):
                model_data[
                    "motion_state/" + str(state_id)
                ] = self.build_base_model_data_from_prototype(
                    first_state_prototype, workflow.get("first_state_fields", [])
                )
            else:
                model_data["motion_state/" + str(state_id)] = {}
            workflow_id += 1
            state_id += 3
            if motion_settings := setting.get("motions"):
                motion_ids = [id_ for id_ in motion_settings]
                meeting_data["motion_ids"] = motion_ids
                all_amendment_ids = []
                for motion_id in motion_ids:
                    motion_setting = motion_settings[motion_id]
                    motion_data = {
                        "title": "Title" + str(motion_id),
                        "text": "<p>Text</p>",
                        "meeting_id": meeting_id,
                    }
                    if motion_setting.get("has_number"):
                        motion_data["number"] = "NUM" + str(motion_number_value)
                        motion_number_value += 1
                    if amendment_settings := motion_setting.get("amendments"):
                        amendment_ids = [id_ for id_ in amendment_settings]
                        all_amendment_ids.extend(amendment_ids)
                        for amendment_id in amendment_ids:
                            amendment_setting = amendment_settings[amendment_id]
                            amendment_data = {
                                **self.build_base_model_data_from_prototype(
                                    amendment_prototype, amendment_setting["fields"]
                                ),
                                "title": "Amendment to " + str(motion_data["title"]),
                                "meeting_id": meeting_id,
                                "lead_motion_id": motion_id,
                            }
                            if amendment_setting.get("has_number"):
                                amendment_data["number"] = "AMNDMNT" + str(
                                    amendment_number_value
                                )
                                amendment_number_value += 1
                            model_data["motion/" + str(amendment_id)] = amendment_data
                    model_data["motion/" + str(motion_id)] = motion_data
                meeting_data["motion_ids"].extend(all_amendment_ids)
            model_data["meeting/" + str(meeting_id)] = meeting_data
        self.set_models(model_data)

    def get_base_meeting_setting(
        self,
        base_motion_id: int,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> SetupMeetingSetting:
        setting: SetupMeetingSetting = {
            "fields": ["name", "is_active_in_organization_id"],
            "motions": {
                base_motion_id: {},
                (base_motion_id + 1): {
                    "has_number": True,
                    "amendments": {
                        (base_motion_id + 2): {
                            "fields": ["amendment_paragraphs"],
                            "has_number": True,
                        },
                        (base_motion_id + 3): {"fields": ["text"], "has_number": True},
                    },
                },
            },
        }
        if is_reason_required:
            setting["fields"].append("motions_reason_required")
        if is_set_number:
            setting["workflow"] = {"first_state_fields": ["set_number"]}
        return setting

    def test_json_upload_empty_data(self) -> None:
        response = self.request(
            "motion.json_upload",
            {"data": [], "meeting_id": 42},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 1 items" in response.json["message"]

    def assert_simple_create(
        self,
        meeting_id: int,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> None:
        self.set_up_models(
            {42: self.get_base_meeting_setting(223, is_reason_required, is_set_number)}
        )
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my", "reason": "stuff"}],
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "meeting_id": meeting_id,
                "title": {"value": "test", "info": ImportState.DONE},
                "text": {"value": "<p>my</p>", "info": ImportState.DONE},
                "reason": {"value": "stuff", "info": ImportState.DONE},
                "submitter_usernames": [
                    {"id": 1, "info": "generated", "value": "admin"}
                ],
            },
        }

    def test_json_upload_simple_create(self) -> None:
        self.assert_simple_create(42)

    def test_json_upload_simple_create_reason_required(self) -> None:
        self.assert_simple_create(42, is_reason_required=True)

    def test_json_upload_simple_create_set_number(self) -> None:
        self.assert_simple_create(42, is_set_number=True)

    def test_json_upload_simple_create_reason_required_and_set_number(
        self,
    ) -> None:
        self.assert_simple_create(42, is_reason_required=True, is_set_number=True)

    def test_json_upload_create_missing_title(self) -> None:
        self.set_up_models({42: self.get_base_meeting_setting(223)})
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"text": "my", "reason": "stuff"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        assert (
            "Error: Title is required"
            in response.json["results"][0][0]["rows"][0]["messages"]
        )

    def test_json_upload_create_missing_text(self) -> None:
        self.set_up_models({42: self.get_base_meeting_setting(223)})
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "reason": "stuff"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        assert (
            "Error: Text is required"
            in response.json["results"][0][0]["rows"][0]["messages"]
        )

    def test_json_upload_create_missing_reason(self) -> None:
        self.set_up_models({42: self.get_base_meeting_setting(223)})
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "meeting_id": 42,
                "title": {"value": "test", "info": ImportState.DONE},
                "text": {"value": "<p>my</p>", "info": ImportState.DONE},
                "submitter_usernames": [
                    {"id": 1, "info": "generated", "value": "admin"}
                ],
            },
        }
