from typing import Any, Dict, List, TypedDict

from typing_extensions import NotRequired

from openslides_backend.action.mixins.import_mixins import ImportState
from tests.system.action.base import BaseActionTestCase

SetupAmendmentSetting = TypedDict(
    "SetupAmendmentSetting",
    {
        "fields": List[str],
        "has_number": NotRequired[bool],
        "category_id": NotRequired[int],
    },
)

SetupMotionSetting = TypedDict(
    "SetupMotionSetting",
    {
        "amendments": NotRequired[Dict[int, SetupAmendmentSetting]],
        "has_number": NotRequired[bool],
        "category_id": NotRequired[int],
    },
)

SetupWorkflowSetting = TypedDict(
    "SetupWorkflowSetting",
    {"first_state_fields": List[str]},
)

SetupCategorySetting = TypedDict(
    "SetupCategorySetting", {"name": str, "prefix": NotRequired[str]}
)

SetupMeetingSetting = TypedDict(
    "SetupMeetingSetting",
    {
        "fields": List[str],
        "motions": NotRequired[Dict[int, SetupMotionSetting]],
        "categories": NotRequired[Dict[int, SetupCategorySetting]],
        "workflow": NotRequired[SetupWorkflowSetting],
        "set_number": NotRequired[bool],
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
        model_data: Dict[str, Any] = {}
        next_ids = {"workflow": 1, "state": 1}
        meeting_prototype = {
            "name": "test",
            "is_active_in_organization_id": 1,
            "motions_reason_required": True,
            "motions_number_type": "per_category",
            "motions_number_min_digits": 2,
        }
        for meeting_id in meetings:
            setting = meetings[meeting_id]
            meeting_data = {
                **self.build_base_model_data_from_prototype(
                    meeting_prototype, setting["fields"]
                ),
                "name": "test meeting" + str(meeting_id),
            }
            self.set_up_workflow(
                model_data,
                meeting_data,
                meeting_id,
                next_ids,
                setting.get("set_number", False),
            )
            if category_settings := setting.get("categories"):
                self.set_up_categories(
                    model_data, meeting_id, meeting_data, category_settings
                )
            if motion_settings := setting.get("motions"):
                self.set_up_motions(
                    model_data, meeting_id, meeting_data, motion_settings
                )
            model_data["meeting/" + str(meeting_id)] = meeting_data
        self.set_models(model_data)

    def set_up_categories(
        self,
        model_data: Dict[str, Any],
        meeting_id: int,
        meeting_data: Dict[str, Any],
        category_settings: Dict[int, SetupCategorySetting],
    ) -> None:
        category_ids = [id_ for id_ in category_settings]
        meeting_data["motion_category_ids"] = category_ids
        for id_ in category_ids:
            category = category_settings[id_]
            category_data = {
                "meeting_id": meeting_id,
                "name": category["name"],
                "motion_ids": [],
            }
            if category.get("prefix"):
                category_data["prefix"] = category["prefix"]
            model_data["motion_category/" + str(id_)] = category_data

    def set_up_motions(
        self,
        model_data: Dict[str, Any],
        meeting_id: int,
        meeting_data: Dict[str, Any],
        motion_settings: Dict[int, SetupMotionSetting],
    ) -> None:
        amendment_prototype = {
            "amendment_paragraphs": {"1": "one"},
            "text": "<p>I am an amendment 2</p>",
        }
        motion_ids = [id_ for id_ in motion_settings]
        meeting_data["motion_ids"] = motion_ids
        motion_number_value = 1
        amendment_number_value = 1
        for motion_id in motion_ids.copy():
            motion_setting = motion_settings[motion_id]
            motion_data = {
                "title": "Title" + str(motion_id),
                "text": "<p>Text</p>",
                "meeting_id": meeting_id,
            }
            if motion_setting.get("has_number"):
                motion_data = {
                    **motion_data,
                    "number": "NUM0" + str(motion_number_value),
                    "number_value": motion_number_value,
                }
                motion_number_value += 1
            if motion_setting.get("category_id"):
                category_id = motion_setting["category_id"]
                motion_data["category_id"] = category_id
                model_data["motion_category/" + str(category_id)]["motion_ids"].append(
                    motion_id
                )
            if amendment_settings := motion_setting.get("amendments"):
                amendment_ids = [id_ for id_ in amendment_settings]
                motion_ids.extend(amendment_ids)
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
                        amendment_data = {
                            **amendment_data,
                            "number": "AMNDMNT" + str(amendment_number_value),
                            "number_value": amendment_number_value,
                        }
                        amendment_number_value += 1
                    if amendment_setting.get("category_id"):
                        category_id = amendment_setting["category_id"]
                        amendment_data["category_id"] = category_id
                        model_data["motion_category/" + str(category_id)][
                            "motion_ids"
                        ].append(amendment_id)
                    model_data["motion/" + str(amendment_id)] = amendment_data
            model_data["motion/" + str(motion_id)] = motion_data

    def set_up_workflow(
        self,
        model_data: Dict[str, Any],
        meeting_data: Dict[str, Any],
        meeting_id: int,
        next_ids: Dict[str, int],
        is_set_number: bool,
    ) -> None:
        workflow_id = next_ids["workflow"]
        state_id = next_ids["state"]
        meeting_data["motions_default_workflow_id"] = workflow_id
        model_data["motion_workflow/" + str(workflow_id)] = {
            "default_workflow_meeting_id": meeting_id,
            "state_ids": [state_id, state_id + 1, state_id + 2],
            "first_state_id": state_id,
            "meeting_id": meeting_id,
        }
        state_data: Dict[str, Any] = {
            "meeting_id": meeting_id,
            "workflow_id": workflow_id,
            "first_state_of_workflow_id": workflow_id,
        }
        if is_set_number:
            state_data = {**state_data, "set_number": True}
        model_data["motion_state/" + str(state_id)] = state_data
        model_data["motion_state/" + str(state_id + 1)] = {
            "meeting_id": meeting_id,
            "workflow_id": workflow_id,
        }
        model_data["motion_state/" + str(state_id + 2)] = {
            "meeting_id": meeting_id,
            "workflow_id": workflow_id,
        }
        next_ids["workflow"] += 1
        next_ids["state"] += 3

    def get_base_meeting_setting(
        self,
        base_motion_id: int,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> SetupMeetingSetting:
        setting: SetupMeetingSetting = {
            "fields": [
                "name",
                "is_active_in_organization_id",
                "motions_number_type",
                "motions_number_min_digits",
            ],
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
                (base_motion_id + 4): {
                    "has_number": True,
                },
            },
        }
        if is_reason_required:
            setting["fields"].append("motions_reason_required")
        if is_set_number:
            setting["set_number"] = True
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
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> None:
        meeting_id = 42
        self.set_up_models(
            {
                meeting_id: self.get_base_meeting_setting(
                    223, is_reason_required, is_set_number
                )
            }
        )
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my", "reason": "stuff"}],
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 1
        data = {
            "meeting_id": meeting_id,
            "title": {"value": "test", "info": ImportState.DONE},
            "text": {"value": "<p>my</p>", "info": ImportState.DONE},
            "reason": {"value": "stuff", "info": ImportState.DONE},
            "submitter_usernames": [{"id": 1, "info": "generated", "value": "admin"}],
        }
        if is_set_number:
            data.update({"number": {"info": ImportState.GENERATED, "value": "03"}})
        expected = {
            "state": ImportState.NEW,
            "messages": [],
            "data": data,
        }
        assert response.json["results"][0][0]["rows"][0] == expected

    def test_json_upload_simple_create(self) -> None:
        self.assert_simple_create()

    def test_json_upload_simple_create_reason_required(self) -> None:
        self.assert_simple_create(is_reason_required=True)

    def test_json_upload_simple_create_set_number(self) -> None:
        self.assert_simple_create(is_set_number=True)

    def test_json_upload_simple_create_reason_required_and_set_number(
        self,
    ) -> None:
        self.assert_simple_create(is_reason_required=True, is_set_number=True)

    def assert_simple_update(
        self,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> None:
        meeting_id = 42
        self.set_up_models(
            {
                meeting_id: self.get_base_meeting_setting(
                    223, is_reason_required, is_set_number
                )
            }
        )
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "number": "NUM01",
                        "title": "test",
                        "text": "my",
                        "reason": "stuff",
                    }
                ],
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 1
        expected = {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "id": 224,
                "meeting_id": meeting_id,
                "number": {"id": 224, "value": "NUM01", "info": ImportState.DONE},
                "title": {"value": "test", "info": ImportState.DONE},
                "text": {"value": "<p>my</p>", "info": ImportState.DONE},
                "reason": {"value": "stuff", "info": ImportState.DONE},
                "submitter_usernames": [
                    {"id": 1, "info": "generated", "value": "admin"}
                ],
            },
        }
        assert response.json["results"][0][0]["rows"][0] == expected

    def test_json_upload_simple_update(self) -> None:
        self.assert_simple_update()

    def test_json_upload_simple_update_reason_required(self) -> None:
        self.assert_simple_update(is_reason_required=True)

    def test_json_upload_simple_update_set_number(self) -> None:
        self.assert_simple_update(is_set_number=True)

    def test_json_upload_simple_update_reason_required_and_set_number(
        self,
    ) -> None:
        self.assert_simple_update(is_reason_required=True, is_set_number=True)

    def assert_dual_simple_create(
        self,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> None:
        meeting_id = 42
        self.set_up_models(
            {
                meeting_id: self.get_base_meeting_setting(
                    223, is_reason_required, is_set_number
                )
            }
        )
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {"title": "test", "text": "my", "reason": "stuff"},
                    {
                        "title": "test also",
                        "text": "<p>my other</p>",
                        "reason": "stuff",
                    },
                ],
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 2
        data = {
            "meeting_id": meeting_id,
            "title": {"value": "test", "info": ImportState.DONE},
            "text": {"value": "<p>my</p>", "info": ImportState.DONE},
            "reason": {"value": "stuff", "info": ImportState.DONE},
            "submitter_usernames": [{"id": 1, "info": "generated", "value": "admin"}],
        }
        if is_set_number:
            data.update({"number": {"info": ImportState.GENERATED, "value": "03"}})
        expected = {
            "state": ImportState.NEW,
            "messages": [],
            "data": data,
        }
        assert response.json["results"][0][0]["rows"][0] == expected
        data = {
            "meeting_id": meeting_id,
            "title": {"value": "test also", "info": ImportState.DONE},
            "text": {"value": "<p>my other</p>", "info": ImportState.DONE},
            "reason": {"value": "stuff", "info": ImportState.DONE},
            "submitter_usernames": [{"id": 1, "info": "generated", "value": "admin"}],
        }
        if is_set_number:
            data.update({"number": {"info": ImportState.GENERATED, "value": "04"}})
        expected = {
            "state": ImportState.NEW,
            "messages": [],
            "data": data,
        }
        assert response.json["results"][0][0]["rows"][1] == expected

    def test_json_upload_dual_create(self) -> None:
        self.assert_dual_simple_create()

    def test_json_upload_dual_create_reason_required(self) -> None:
        self.assert_dual_simple_create(is_reason_required=True)

    def test_json_upload_dual_create_set_number(self) -> None:
        self.assert_dual_simple_create(is_set_number=True)

    def test_json_upload_dual_create_reason_required_and_set_number(
        self,
    ) -> None:
        self.assert_dual_simple_create(is_reason_required=True, is_set_number=True)

    def assert_dual_simple_update(
        self,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> None:
        meeting_id = 42
        self.set_up_models(
            {
                meeting_id: self.get_base_meeting_setting(
                    223, is_reason_required, is_set_number
                )
            }
        )
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "number": "NUM01",
                        "title": "test",
                        "text": "my",
                        "reason": "stuff",
                    },
                    {
                        "number": "NUM02",
                        "title": "test also",
                        "text": "<p>my other</p>",
                        "reason": "stuff",
                    },
                ],
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 2
        expected = {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "id": 224,
                "meeting_id": meeting_id,
                "number": {"id": 224, "value": "NUM01", "info": ImportState.DONE},
                "title": {"value": "test", "info": ImportState.DONE},
                "text": {"value": "<p>my</p>", "info": ImportState.DONE},
                "reason": {"value": "stuff", "info": ImportState.DONE},
                "submitter_usernames": [
                    {"id": 1, "info": "generated", "value": "admin"}
                ],
            },
        }
        assert response.json["results"][0][0]["rows"][0] == expected

    def test_json_upload_dual_update(self) -> None:
        self.assert_dual_simple_update()

    def test_json_upload_dual_update_reason_required(self) -> None:
        self.assert_dual_simple_update(is_reason_required=True)

    def test_json_upload_dual_update_set_number(self) -> None:
        self.assert_dual_simple_update(is_set_number=True)

    def test_json_upload_dual_update_reason_required_and_set_number(
        self,
    ) -> None:
        self.assert_dual_simple_update(is_reason_required=True, is_set_number=True)

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

        assert response.json["results"][0][0]["rows"][0]["data"]["title"] == {
            "value": "",
            "info": ImportState.ERROR,
        }

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
        assert response.json["results"][0][0]["rows"][0]["data"]["text"] == {
            "value": "",
            "info": ImportState.ERROR,
        }

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

    def test_json_upload_create_missing_reason_although_required(self) -> None:
        self.set_up_models(
            {42: self.get_base_meeting_setting(223, is_reason_required=True)}
        )
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        assert (
            "Error: Reason is required"
            in response.json["results"][0][0]["rows"][0]["messages"]
        )
        assert response.json["results"][0][0]["rows"][0]["data"]["reason"] == {
            "value": "",
            "info": ImportState.ERROR,
        }

    def assert_custom_number_create(
        self, is_set_number: bool = False
    ) -> List[Dict[str, Any]]:
        self.set_up_models(
            {42: self.get_base_meeting_setting(223, is_set_number=is_set_number)}
        )
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {"number": "Z01", "title": "test", "text": "my", "reason": "stuff"}
                ],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        return response.json["results"][0][0]["rows"]

    def test_json_upload_custom_number_create(self) -> None:
        rows = self.assert_custom_number_create()
        assert len(rows) == 1
        assert rows[0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "meeting_id": 42,
                "number": {"value": "Z01", "info": ImportState.DONE},
                "text": {"value": "<p>my</p>", "info": ImportState.DONE},
                "title": {"value": "test", "info": ImportState.DONE},
                "reason": {"value": "stuff", "info": ImportState.DONE},
                "submitter_usernames": [
                    {"id": 1, "info": "generated", "value": "admin"}
                ],
            },
        }

    def test_json_upload_custom_number_create_with_set_number(self) -> None:
        rows = self.assert_custom_number_create(True)
        assert len(rows) == 1
        assert rows[0] == {
            "state": ImportState.NEW,
            "messages": [],
            "data": {
                "meeting_id": 42,
                "number": {"value": "Z01", "info": ImportState.DONE},
                "title": {"value": "test", "info": ImportState.DONE},
                "text": {"value": "<p>my</p>", "info": ImportState.DONE},
                "reason": {"value": "stuff", "info": ImportState.DONE},
                "submitter_usernames": [
                    {"id": 1, "info": "generated", "value": "admin"}
                ],
            },
        }

    def assert_duplicate_numbers(self, number: str) -> None:
        meeting_id = 42
        self.set_up_models({meeting_id: self.get_base_meeting_setting(223)})
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "number": number,
                        "title": "test",
                        "text": "my",
                        "reason": "stuff",
                    },
                    {
                        "number": number,
                        "title": "test also",
                        "text": "<p>my other</p>",
                        "reason": "stuff",
                    },
                ],
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 2
        result = response.json["results"][0][0]
        assert result["state"] == ImportState.ERROR
        for i in [0, 1]:
            assert result["rows"][i]["state"] == ImportState.ERROR
            assert (
                "Error: Found multiple motions with the same number"
                in result["rows"][i]["messages"]
            )
            assert result["rows"][i]["data"]["number"] == {
                "value": number,
                "info": ImportState.ERROR,
            }

    def test_json_upload_duplicate_numbers_create(self) -> None:
        self.assert_duplicate_numbers("NUM04")

    def test_json_upload_duplicate_numbers_update(self) -> None:
        self.assert_duplicate_numbers("NUM01")

    def extend_meeting_setting_with_categories(
        self,
        setting: SetupMeetingSetting,
        categories: Dict[int, SetupCategorySetting],
        motion_to_category_ids: Dict[int, int],
    ) -> SetupMeetingSetting:
        setting["categories"] = categories
        if setting.get("motions"):
            for motion_id in setting["motions"]:
                motion = setting["motions"][motion_id]
                self.add_category_id(motion_id, motion, motion_to_category_ids)
                if motion.get("amendments"):
                    for amendment_id in motion["amendments"]:
                        self.add_category_id(
                            amendment_id,
                            motion["amendments"][amendment_id],
                            motion_to_category_ids,
                        )
        return setting

    def add_category_id(
        self,
        motion_id: int,
        motion: Any,
        motion_to_category_ids: Dict[int, int],
    ) -> None:
        if motion_to_category_ids.get(motion_id):
            motion["category_id"] = motion_to_category_ids[motion_id]

    def get_category_extended_base_meeting_setting(
        self,
        base_motion_id: int,
        base_category_id: int,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> SetupMeetingSetting:
        return self.extend_meeting_setting_with_categories(
            self.get_base_meeting_setting(
                base_motion_id, is_reason_required, is_set_number
            ),
            {
                base_category_id: {
                    "name": "General category",
                    "prefix": "NUM",
                },
                (base_category_id + 1): {
                    "name": "Amendment category",
                    "prefix": "AMNDMNT",
                },
                (base_category_id + 2): {
                    "name": "Empty category",
                },
                (base_category_id + 3): {
                    "name": "Amendment category 2",
                    "prefix": "AMNDMNT",
                },
                (base_category_id + 4): {
                    "name": "General category",
                    "prefix": "COPY",
                },
                (base_category_id + 5): {
                    "name": "Another category",
                    "prefix": "CAT",
                },
                (base_category_id + 6): {
                    "name": "General category",
                },
                (base_category_id + 7): {
                    "name": "Duplicate category",
                    "prefix": "DUPE",
                },
                (base_category_id + 8): {
                    "name": "Duplicate category",
                    "prefix": "DUPE",
                },
            },
            {
                base_motion_id: (base_category_id + 2),
                (base_motion_id + 1): base_category_id,
                (base_motion_id + 1): (base_category_id + 1),
                (base_motion_id + 1): (base_category_id + 3),
                (base_motion_id + 1): base_category_id,
            },
        )

    def assert_with_categories(
        self,
        is_update: bool = False,
        request_with_numbers: bool = False,
        is_set_number: bool = False,
    ) -> None:
        meeting_id = 42
        self.set_up_models(
            {
                meeting_id: self.get_category_extended_base_meeting_setting(
                    223, 2223, False, is_set_number
                )
            }
        )
        data: List[Dict[str, Any]] = list(
            (
                {
                    "title": "test",
                    "text": "my",
                    "reason": "stuff",
                    "category_name": "Another category",
                    "category_prefix": "CAT",
                },
                {
                    "title": "test also",
                    "text": "<p>my other</p>",
                    "reason": "stuff",
                    "category_name": "Another category",
                    "category_prefix": "CAT",
                },
            ),
        )
        if is_update:
            for i in range(len(data)):
                data[i]["number"] = "NUM0" + str(i + 1)
        elif request_with_numbers:
            for i in range(len(data)):
                data[i]["number"] = "NOM0" + str(i + 1)
        response = self.request(
            "motion.json_upload",
            {
                "data": data,
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        rows = response.json["results"][0][0]["rows"]
        assert len(rows) == 2
        for i in range(2):
            assert (
                rows[i]["state"] == ImportState.DONE if is_update else ImportState.NEW
            )
            assert rows[i]["data"]["category_name"] == {
                "id": 2228,
                "info": "done",
                "value": "Another category",
            }
            assert rows[i]["data"]["category_prefix"] == "CAT"
            if is_update:
                assert rows[i]["data"].get("number") == {
                    "id": 224 if i == 0 else 227,
                    "info": ImportState.DONE,
                    "value": "NUM0" + str(i + 1),
                }
            elif request_with_numbers:
                assert rows[i]["data"].get("number") == {
                    "info": ImportState.DONE,
                    "value": "NOM0" + str(i + 1),
                }
            elif is_set_number:
                assert rows[i]["data"].get("number") == {
                    "info": ImportState.GENERATED,
                    "value": "CAT0" + str(i + 1),
                }
            else:
                assert rows[i]["data"].get("number") is None

    def test_json_upload_create_with_categories(self) -> None:
        self.assert_with_categories()

    def test_json_upload_update_with_categories(self) -> None:
        self.assert_with_categories(True)

    def test_json_upload_create_with_categories_with_numbers(self) -> None:
        self.assert_with_categories(request_with_numbers=True)

    def test_json_upload_create_with_categories_with_set_number(self) -> None:
        self.assert_with_categories(is_set_number=True)

    def test_json_upload_update_with_categories_with_set_number(self) -> None:
        self.assert_with_categories(True, is_set_number=True)

    def test_json_upload_create_with_categories_with_numbers_and_set_number(
        self,
    ) -> None:
        self.assert_with_categories(request_with_numbers=True, is_set_number=True)

    def get_response_for_categories_no_prefix(
        self,
        name: str,
        is_update: bool = False,
        request_with_numbers: bool = False,
        is_set_number: bool = False,
    ) -> Any:
        meeting_id = 42
        self.set_up_models(
            {
                meeting_id: self.get_category_extended_base_meeting_setting(
                    223, 2223, False, is_set_number
                )
            }
        )
        data: List[Dict[str, Any]] = list(
            (
                {
                    "title": "New title",
                    "text": "New text",
                    "reason": "New reason",
                    "category_name": name,
                },
            ),
        )
        if is_update:
            data[0]["number"] = "NUM01"
        elif request_with_numbers:
            data[0]["number"] = "NOM01"
        response = self.request(
            "motion.json_upload",
            {
                "data": data,
                "meeting_id": meeting_id,
            },
        )
        return response

    def assert_with_categories_no_prefix(
        self,
        is_update: bool = False,
        request_with_numbers: bool = False,
        is_set_number: bool = False,
    ) -> None:
        response = self.get_response_for_categories_no_prefix(
            "Empty category", is_update, request_with_numbers, is_set_number
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        rows = response.json["results"][0][0]["rows"]
        assert len(rows) == 1
        assert rows[0]["state"] == ImportState.DONE if is_update else ImportState.NEW
        assert rows[0]["data"]["category_name"] == {
            "id": 2225,
            "info": "done",
            "value": "Empty category",
        }
        assert rows[0]["data"].get("category_prefix") is None
        if is_update:
            assert rows[0]["data"].get("number") == {
                "id": 224,
                "info": ImportState.DONE,
                "value": "NUM01",
            }
        elif request_with_numbers:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.DONE,
                "value": "NOM01",
            }
        elif is_set_number:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.GENERATED,
                "value": "01",
            }
        else:
            assert rows[0]["data"].get("number") is None

    def test_json_upload_create_with_categories_no_prefix(self) -> None:
        self.assert_with_categories_no_prefix()

    def test_json_upload_update_with_categories_no_prefix(self) -> None:
        self.assert_with_categories_no_prefix(True)

    def test_json_upload_create_with_categories_with_numbers_no_prefix(self) -> None:
        self.assert_with_categories_no_prefix(request_with_numbers=True)

    def test_json_upload_create_with_categories_with_set_number_no_prefix(self) -> None:
        self.assert_with_categories_no_prefix(is_set_number=True)

    def test_json_upload_update_with_categories_with_set_number_no_prefix(self) -> None:
        self.assert_with_categories_no_prefix(True, is_set_number=True)

    def test_json_upload_create_with_categories_with_numbers_and_set_number_no_prefix(
        self,
    ) -> None:
        self.assert_with_categories_no_prefix(
            request_with_numbers=True, is_set_number=True
        )

    def assert_with_categories_no_prefix_find_correct(
        self,
        is_update: bool = False,
        request_with_numbers: bool = False,
        is_set_number: bool = False,
    ) -> None:
        response = self.get_response_for_categories_no_prefix(
            "General category", is_update, request_with_numbers, is_set_number
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        rows = response.json["results"][0][0]["rows"]
        assert len(rows) == 1
        assert rows[0]["state"] == ImportState.DONE if is_update else ImportState.NEW
        assert rows[0]["data"]["category_name"] == {
            "id": 2229,
            "info": "done",
            "value": "General category",
        }
        assert rows[0]["data"].get("category_prefix") is None
        if is_update:
            assert rows[0]["data"].get("number") == {
                "id": 224,
                "info": ImportState.DONE,
                "value": "NUM01",
            }
        elif request_with_numbers:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.DONE,
                "value": "NOM01",
            }
        elif is_set_number:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.GENERATED,
                "value": "01",
            }
        else:
            assert rows[0]["data"].get("number") is None

    def test_json_upload_create_with_categories_no_prefix_find_correct(self) -> None:
        self.assert_with_categories_no_prefix_find_correct()

    def test_json_upload_update_with_categories_no_prefix_find_correct(self) -> None:
        self.assert_with_categories_no_prefix_find_correct(True)

    def test_json_upload_create_with_categories_with_numbers_no_prefix_find_correct(
        self,
    ) -> None:
        self.assert_with_categories_no_prefix_find_correct(request_with_numbers=True)

    def test_json_upload_create_with_categories_with_set_number_no_prefix_find_correct(
        self,
    ) -> None:
        self.assert_with_categories_no_prefix_find_correct(is_set_number=True)

    def test_json_upload_update_with_categories_with_set_number_no_prefix_find_correct(
        self,
    ) -> None:
        self.assert_with_categories_no_prefix_find_correct(True, is_set_number=True)

    def test_json_upload_create_with_categories_with_numbers_and_set_number_no_prefix_find_correct(
        self,
    ) -> None:
        self.assert_with_categories_no_prefix_find_correct(
            request_with_numbers=True, is_set_number=True
        )

    def assert_with_categories_no_prefix_with_warning(
        self,
        is_update: bool = False,
        request_with_numbers: bool = False,
        is_set_number: bool = False,
    ) -> None:
        response = self.get_response_for_categories_no_prefix(
            "Another category", is_update, request_with_numbers, is_set_number
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.WARNING
        rows = response.json["results"][0][0]["rows"]
        assert len(rows) == 1
        assert rows[0]["state"] == ImportState.DONE if is_update else ImportState.NEW
        assert rows[0]["data"]["category_name"] == {
            "info": ImportState.WARNING,
            "value": "Another category",
        }
        assert rows[0]["data"].get("category_prefix") is None
        assert "Category could not be found" in rows[0]["messages"]
        if is_update:
            assert rows[0]["data"].get("number") == {
                "id": 224,
                "info": ImportState.DONE,
                "value": "NUM01",
            }
        elif request_with_numbers:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.DONE,
                "value": "NOM01",
            }
        elif is_set_number:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.GENERATED,
                "value": "03",
            }
        else:
            assert rows[0]["data"].get("number") is None

    def test_json_upload_create_with_categories_no_prefix_with_warning(self) -> None:
        self.assert_with_categories_no_prefix_with_warning()

    def test_json_upload_update_with_categories_no_prefix_with_warning(self) -> None:
        self.assert_with_categories_no_prefix_with_warning(True)

    def test_json_upload_create_with_categories_with_numbers_no_prefix_with_warning(
        self,
    ) -> None:
        self.assert_with_categories_no_prefix_with_warning(request_with_numbers=True)

    def test_json_upload_create_with_categories_with_set_number_no_prefix_with_warning(
        self,
    ) -> None:
        self.assert_with_categories_no_prefix_with_warning(is_set_number=True)

    def test_json_upload_update_with_categories_with_set_number_no_prefix_with_warning(
        self,
    ) -> None:
        self.assert_with_categories_no_prefix_with_warning(True, is_set_number=True)

    def test_json_upload_create_with_categories_with_numbers_and_set_number_no_prefix_with_warning(
        self,
    ) -> None:
        self.assert_with_categories_no_prefix_with_warning(
            request_with_numbers=True, is_set_number=True
        )

    def assert_with_categories_no_name(
        self,
        is_update: bool = False,
        request_with_numbers: bool = False,
        is_set_number: bool = False,
    ) -> None:
        meeting_id = 42
        self.set_up_models(
            {
                meeting_id: self.get_category_extended_base_meeting_setting(
                    223, 2223, False, is_set_number
                )
            }
        )
        data: List[Dict[str, Any]] = list(
            (
                {
                    "title": "test",
                    "text": "my",
                    "reason": "stuff",
                    "category_prefix": "COPY",
                },
            ),
        )
        if is_update:
            data[0]["number"] = "NUM01"
        elif request_with_numbers:
            data[0]["number"] = "NOM01"
        response = self.request(
            "motion.json_upload",
            {
                "data": data,
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.WARNING
        rows = response.json["results"][0][0]["rows"]
        assert len(rows) == 1
        assert rows[0]["state"] == ImportState.DONE if is_update else ImportState.NEW
        assert rows[0]["data"]["category_name"] == {
            "info": ImportState.WARNING,
            "value": "",
        }
        assert rows[0]["data"]["category_prefix"] == "COPY"
        assert "Category could not be found" in rows[0]["messages"]
        if is_update:
            assert rows[0]["data"].get("number") == {
                "id": 224,
                "info": ImportState.DONE,
                "value": "NUM01",
            }
        elif request_with_numbers:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.DONE,
                "value": "NOM01",
            }
        elif is_set_number:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.GENERATED,
                "value": "03",
            }
        else:
            assert rows[0]["data"].get("number") is None

    def test_json_upload_create_with_categories_no_name(self) -> None:
        self.assert_with_categories_no_name()

    def test_json_upload_update_with_categories_no_name(self) -> None:
        self.assert_with_categories_no_name(True)

    def test_json_upload_create_with_categories_with_numbers_no_name(self) -> None:
        self.assert_with_categories_no_name(request_with_numbers=True)

    def test_json_upload_create_with_categories_with_set_number_no_name(self) -> None:
        self.assert_with_categories_no_name(is_set_number=True)

    def test_json_upload_update_with_categories_with_set_number_no_name(self) -> None:
        self.assert_with_categories_no_name(True, is_set_number=True)

    def test_json_upload_create_with_categories_with_numbers_and_set_number_no_name(
        self,
    ) -> None:
        self.assert_with_categories_no_name(
            request_with_numbers=True, is_set_number=True
        )

    def assert_with_categories_with_warning(
        self,
        is_update: bool = False,
        request_with_numbers: bool = False,
        is_set_number: bool = False,
    ) -> None:
        meeting_id = 42
        self.set_up_models(
            {
                meeting_id: self.get_category_extended_base_meeting_setting(
                    223, 2223, False, is_set_number
                )
            }
        )
        data: List[Dict[str, Any]] = list(
            (
                {
                    "title": "test",
                    "text": "my",
                    "reason": "stuff",
                    "category_name": "Unknown category",
                    "category_prefix": "UNKNWN",
                },
            ),
        )
        if is_update:
            data[0]["number"] = "NUM01"
        elif request_with_numbers:
            data[0]["number"] = "NOM01"
        response = self.request(
            "motion.json_upload",
            {
                "data": data,
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.WARNING
        rows = response.json["results"][0][0]["rows"]
        assert len(rows) == 1
        assert rows[0]["state"] == ImportState.DONE if is_update else ImportState.NEW
        assert rows[0]["data"]["category_name"] == {
            "info": ImportState.WARNING,
            "value": "Unknown category",
        }
        assert rows[0]["data"]["category_prefix"] == "UNKNWN"
        assert "Category could not be found" in rows[0]["messages"]
        if is_update:
            assert rows[0]["data"].get("number") == {
                "id": 224,
                "info": ImportState.DONE,
                "value": "NUM01",
            }
        elif request_with_numbers:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.DONE,
                "value": "NOM01",
            }
        elif is_set_number:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.GENERATED,
                "value": "03",
            }
        else:
            assert rows[0]["data"].get("number") is None

    def test_json_upload_create_with_categories_with_warning(self) -> None:
        self.assert_with_categories_with_warning()

    def test_json_upload_update_with_categories_with_warning(self) -> None:
        self.assert_with_categories_with_warning(True)

    def test_json_upload_create_with_categories_with_numbers_with_warning(self) -> None:
        self.assert_with_categories_with_warning(request_with_numbers=True)

    def test_json_upload_create_with_categories_with_set_number_with_warning(
        self,
    ) -> None:
        self.assert_with_categories_with_warning(is_set_number=True)

    def test_json_upload_update_with_categories_with_set_number_with_warning(
        self,
    ) -> None:
        self.assert_with_categories_with_warning(True, is_set_number=True)

    def test_json_upload_create_with_categories_with_numbers_and_set_number_with_warning(
        self,
    ) -> None:
        self.assert_with_categories_with_warning(
            request_with_numbers=True, is_set_number=True
        )

    def assert_with_categories_with_duplicate_categories(
        self,
        is_update: bool = False,
        request_with_numbers: bool = False,
        is_set_number: bool = False,
    ) -> None:
        meeting_id = 42
        self.set_up_models(
            {
                meeting_id: self.get_category_extended_base_meeting_setting(
                    223, 2223, False, is_set_number
                )
            }
        )
        data: List[Dict[str, Any]] = list(
            (
                {
                    "title": "test",
                    "text": "my",
                    "reason": "stuff",
                    "category_name": "Duplicate category",
                    "category_prefix": "DUPE",
                },
            ),
        )
        if is_update:
            data[0]["number"] = "NUM01"
        elif request_with_numbers:
            data[0]["number"] = "NOM01"
        response = self.request(
            "motion.json_upload",
            {
                "data": data,
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.WARNING
        rows = response.json["results"][0][0]["rows"]
        assert len(rows) == 1
        assert rows[0]["state"] == ImportState.DONE if is_update else ImportState.NEW
        assert rows[0]["data"]["category_name"] == {
            "info": ImportState.WARNING,
            "value": "Duplicate category",
        }
        assert rows[0]["data"]["category_prefix"] == "DUPE"
        assert "Category could not be found" in rows[0]["messages"]
        if is_update:
            assert rows[0]["data"].get("number") == {
                "id": 224,
                "info": ImportState.DONE,
                "value": "NUM01",
            }
        elif request_with_numbers:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.DONE,
                "value": "NOM01",
            }
        elif is_set_number:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.GENERATED,
                "value": "03",
            }
        else:
            assert rows[0]["data"].get("number") is None

    def test_json_upload_create_with_categories_with_duplicate_categories(self) -> None:
        self.assert_with_categories_with_duplicate_categories()

    def test_json_upload_update_with_categories_with_duplicate_categories(self) -> None:
        self.assert_with_categories_with_duplicate_categories(True)

    def test_json_upload_create_with_categories_with_numbers_with_duplicate_categories(
        self,
    ) -> None:
        self.assert_with_categories_with_duplicate_categories(request_with_numbers=True)

    def test_json_upload_create_with_categories_with_set_number_with_duplicate_categories(
        self,
    ) -> None:
        self.assert_with_categories_with_duplicate_categories(is_set_number=True)

    def test_json_upload_update_with_categories_with_set_number_with_duplicate_categories(
        self,
    ) -> None:
        self.assert_with_categories_with_duplicate_categories(True, is_set_number=True)

    def test_json_upload_create_with_categories_with_numbers_and_set_number_with_duplicate_categories(
        self,
    ) -> None:
        self.assert_with_categories_with_duplicate_categories(
            request_with_numbers=True, is_set_number=True
        )

    def assert_with_categories_one_of_two_with_same_prefix(
        self,
        is_update: bool = False,
        request_with_numbers: bool = False,
        is_set_number: bool = False,
    ) -> None:
        meeting_id = 42
        self.set_up_models(
            {
                meeting_id: self.get_category_extended_base_meeting_setting(
                    223, 2223, False, is_set_number
                )
            }
        )
        data: List[Dict[str, Any]] = list(
            (
                {
                    "title": "test",
                    "text": "my",
                    "reason": "stuff",
                    "category_name": "Amendment category",
                    "category_prefix": "AMNDMNT",
                },
            ),
        )
        if is_update:
            data[0]["number"] = "NUM01"
        elif request_with_numbers:
            data[0]["number"] = "NOM01"
        response = self.request(
            "motion.json_upload",
            {
                "data": data,
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        rows = response.json["results"][0][0]["rows"]
        assert len(rows) == 1
        assert rows[0]["state"] == ImportState.DONE if is_update else ImportState.NEW
        assert rows[0]["data"]["category_name"] == {
            "id": 2224,
            "info": ImportState.DONE,
            "value": "Amendment category",
        }
        assert rows[0]["data"]["category_prefix"] == "AMNDMNT"
        if is_update:
            assert rows[0]["data"].get("number") == {
                "id": 224,
                "info": ImportState.DONE,
                "value": "NUM01",
            }
        elif request_with_numbers:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.DONE,
                "value": "NOM01",
            }
        elif is_set_number:
            assert rows[0]["data"].get("number") == {
                "info": ImportState.GENERATED,
                "value": "AMNDMNT01",
            }
        else:
            assert rows[0]["data"].get("number") is None

    def test_json_upload_create_with_categories_same_prefix(self) -> None:
        self.assert_with_categories_one_of_two_with_same_prefix()

    def test_json_upload_update_with_categories_same_prefix(self) -> None:
        self.assert_with_categories_one_of_two_with_same_prefix(True)

    def test_json_upload_create_with_categories_with_numbers_same_prefix(self) -> None:
        self.assert_with_categories_one_of_two_with_same_prefix(
            request_with_numbers=True
        )

    def test_json_upload_create_with_categories_with_set_number_same_prefix(
        self,
    ) -> None:
        self.assert_with_categories_one_of_two_with_same_prefix(is_set_number=True)

    def test_json_upload_update_with_categories_with_set_number_same_prefix(
        self,
    ) -> None:
        self.assert_with_categories_one_of_two_with_same_prefix(
            True, is_set_number=True
        )

    def test_json_upload_create_with_categories_with_numbers_and_set_number_same_prefix(
        self,
    ) -> None:
        self.assert_with_categories_one_of_two_with_same_prefix(
            request_with_numbers=True, is_set_number=True
        )
