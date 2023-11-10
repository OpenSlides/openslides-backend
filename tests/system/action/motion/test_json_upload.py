from typing import Any, Dict, List, Optional, Tuple, TypedDict

from typing_extensions import NotRequired

from openslides_backend.action.mixins.import_mixins import ImportState
from tests.system.action.base import BaseActionTestCase

SetupUserSetting = TypedDict(
    "SetupUserSetting",
    {
        "username": str,
        "meeting_ids": NotRequired[List[int]],
        "submitted_motion_ids": NotRequired[List[int]],
        "supported_motion_ids": NotRequired[List[int]],
    },
)

SetupCommonMotionSetting = TypedDict(
    "SetupCommonMotionSetting",
    {
        "has_number": bool,
        "category_id": int,
    },
    total=False,
)

SetupAmendmentSetting = TypedDict(
    "SetupAmendmentSetting",
    {
        "base": SetupCommonMotionSetting,
        "fields": List[str],
    },
)

SetupMotionSetting = TypedDict(
    "SetupMotionSetting",
    {
        "base": SetupCommonMotionSetting,
        "amendments": NotRequired[Dict[int, SetupAmendmentSetting]],
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

    def set_up_models(
        self,
        meetings: Dict[int, SetupMeetingSetting],
        users: Optional[List[SetupUserSetting]] = None,
    ) -> Dict[str, Any]:
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
                "group_ids": [meeting_id * 10],
            }
            model_data["group/" + str(meeting_id * 10)] = {
                "meeting_id": meeting_id,
                "name": "test",
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
        if users:
            for idx, user_setting in enumerate(users):
                self.set_up_user(idx + 2, user_setting, model_data)
        # model_data_keys = list(model_data.keys())
        # model_data_keys.sort()
        # sorted_model_data = { key:model_data[key] for key in model_data_keys}
        self.set_models(model_data)
        return model_data

    def set_up_user(
        self,
        user_id: int,
        setting: SetupUserSetting,
        model_data: Dict[str, Dict[str, Any]],
    ) -> None:
        user_data: Dict[str, Any] = {"username": setting["username"]}
        next_meeting_user_id = user_id * 100
        meeting_ids = setting.get("meeting_ids", [])
        for meeting_id in meeting_ids:
            if meeting := model_data.get("meeting/" + str(meeting_id)):
                next_motion_submitter_id = next_meeting_user_id * 100
                user_data["meeting_user_ids"] = [
                    *user_data.get("meeting_user_ids", []),
                    next_meeting_user_id,
                ]
                meeting_user_data: Dict[str, Any] = {
                    "user_id": user_id,
                    "meeting_id": meeting_id,
                    "group_ids": [meeting_id * 10],
                }
                meeting["meeting_user_ids"] = [
                    *meeting.get("meeting_user_ids", []),
                    next_meeting_user_id,
                ]
                model_data["group/" + str(meeting_id * 10)][
                    "meeting_user_ids"
                ] = meeting["meeting_user_ids"]
                motion_submitter_ids = []
                supported_motion_ids = []
                for motion_id in meeting.get("motion_ids", []):
                    motion = model_data["motion/" + str(motion_id)]
                    if motion_id in setting.get("submitted_motion_ids", []):
                        motion["submitter_ids"] = [
                            *motion.get("submitter_ids", []),
                            next_motion_submitter_id,
                        ]
                        model_data[
                            "motion_submitter/" + str(next_motion_submitter_id)
                        ] = {
                            "motion_id": motion_id,
                            "meeting_id": meeting_id,
                            "meeting_user_id": next_meeting_user_id,
                        }
                        motion_submitter_ids.append(next_motion_submitter_id)
                        next_motion_submitter_id += 1
                    if motion_id in setting.get("supported_motion_ids", []):
                        supported_motion_ids.append(motion_id)
                        motion["supporter_meeting_user_ids"] = [
                            *motion.get("supporter_meeting_user_ids", []),
                            next_meeting_user_id,
                        ]
                if len(supported_motion_ids):
                    meeting_user_data["supported_motion_ids"] = supported_motion_ids
                if len(motion_submitter_ids):
                    meeting_user_data["motion_submitter_ids"] = motion_submitter_ids
                    meeting["motion_submitter_ids"] = [
                        *meeting.get("motion_submitter_ids", []),
                        *motion_submitter_ids,
                    ]
                model_data[
                    "meeting_user/" + str(next_meeting_user_id)
                ] = meeting_user_data
                next_meeting_user_id += 1
        model_data["user/" + str(user_id)] = user_data

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
                category_data["prefix"] = category.get("prefix")
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
            if motion_setting["base"].get("has_number"):
                motion_data = {
                    **motion_data,
                    "number": "NUM0" + str(motion_number_value),
                    "number_value": motion_number_value,
                }
                motion_number_value += 1
            if motion_setting["base"].get("category_id"):
                category_id = motion_setting["base"].get("category_id")
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
                    if amendment_setting["base"].get("has_number"):
                        amendment_data = {
                            **amendment_data,
                            "number": "AMNDMNT" + str(amendment_number_value),
                            "number_value": amendment_number_value,
                        }
                        amendment_number_value += 1
                    if amendment_setting["base"].get("category_id"):
                        category_id = amendment_setting["base"].get("category_id")
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
        meeting_data.update(
            {
                "motions_default_workflow_id": workflow_id,
                "motion_workflow_ids": [workflow_id],
                "motion_state_ids": list(range(state_id, state_id + 3)),
            }
        )
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
                base_motion_id: {"base": {}},
                (base_motion_id + 1): {
                    "base": {"has_number": True},
                    "amendments": {
                        (base_motion_id + 2): {
                            "fields": ["amendment_paragraphs"],
                            "base": {"has_number": True},
                        },
                        (base_motion_id + 3): {
                            "fields": ["text"],
                            "base": {"has_number": True},
                        },
                    },
                },
                (base_motion_id + 4): {
                    "base": {"has_number": True},
                },
            },
        }
        if is_reason_required:
            setting["fields"].append("motions_reason_required")
        if is_set_number:
            setting["set_number"] = True
        return setting

    # -------------------- Basic tests --------------------

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
            "submitters_username": [{"id": 1, "info": "generated", "value": "admin"}],
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
                "submitters_username": [
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
            "submitters_username": [{"id": 1, "info": "generated", "value": "admin"}],
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
            "submitters_username": [{"id": 1, "info": "generated", "value": "admin"}],
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
                "submitters_username": [
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
                "submitters_username": [
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
                "submitters_username": [
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
                "submitters_username": [
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

    # -------------------- Test with categories --------------------

    def extend_meeting_setting_with_categories(
        self,
        setting: SetupMeetingSetting,
        categories: Dict[int, SetupCategorySetting],
        motion_to_category_ids: Dict[int, int],
    ) -> SetupMeetingSetting:
        setting["categories"] = categories
        for motion_id in setting.get("motions", {}):
            motion = setting.get("motions", {})[motion_id]
            self.add_category_id(motion_id, motion, motion_to_category_ids)
            for amendment_id in motion.get("amendments", {}):
                self.add_category_id(
                    amendment_id,
                    motion.get("amendments", {})[amendment_id],
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
            motion["base"]["category_id"] = motion_to_category_ids[motion_id]

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

    def make_conditional_number_assertions_for_category_test(
        self,
        rows: List[Dict[str, Any]],
        is_update: bool = False,
        request_with_numbers: bool = False,
        is_set_number: bool = False,
        ids_for_row_indices: Dict[int, Optional[int]] = {},
        generated_numbers_for_row_indices: Dict[int, Optional[str]] = {},
    ) -> None:
        for i in range(len(rows)):
            if is_update:
                assert rows[i]["data"].get("number") == {
                    "id": ids_for_row_indices[i],
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
                    "value": generated_numbers_for_row_indices[i],
                }
            else:
                assert rows[i]["data"].get("number") is None

    def make_category_request(
        self,
        data: List[Dict[str, Any]],
        meeting_id: int,
        is_update: bool = False,
        request_with_numbers: bool = False,
    ) -> Any:
        if is_update:
            for i in range(len(data)):
                data[i]["number"] = "NUM0" + str(i + 1)
        elif request_with_numbers:
            for i in range(len(data)):
                data[i]["number"] = "NOM0" + str(i + 1)
        return self.request(
            "motion.json_upload",
            {
                "data": data,
                "meeting_id": meeting_id,
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
        response = self.make_category_request(
            data, meeting_id, is_update, request_with_numbers
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        rows = response.json["results"][0][0]["rows"]
        assert len(rows) == 2
        for i in range(len(rows)):
            assert (
                rows[i]["state"] == ImportState.DONE if is_update else ImportState.NEW
            )
            assert rows[i]["data"]["category_name"] == {
                "id": 2228,
                "info": "done",
                "value": "Another category",
            }
            assert rows[i]["data"]["category_prefix"] == "CAT"
        self.make_conditional_number_assertions_for_category_test(
            rows,
            is_update,
            request_with_numbers,
            is_set_number,
            {0: 224, 1: 227},
            {0: "CAT01", 1: "CAT02"},
        )

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
        return self.make_category_request(
            data, meeting_id, is_update, request_with_numbers
        )

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
        self.make_conditional_number_assertions_for_category_test(
            rows, is_update, request_with_numbers, is_set_number, {0: 224}, {0: "01"}
        )

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
        self.make_conditional_number_assertions_for_category_test(
            rows, is_update, request_with_numbers, is_set_number, {0: 224}, {0: "01"}
        )

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
        self.make_conditional_number_assertions_for_category_test(
            rows, is_update, request_with_numbers, is_set_number, {0: 224}, {0: "03"}
        )

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
        response = self.make_category_request(
            data, meeting_id, is_update, request_with_numbers
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
        self.make_conditional_number_assertions_for_category_test(
            rows, is_update, request_with_numbers, is_set_number, {0: 224}, {0: "03"}
        )

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
        response = self.make_category_request(
            data, meeting_id, is_update, request_with_numbers
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
        self.make_conditional_number_assertions_for_category_test(
            rows, is_update, request_with_numbers, is_set_number, {0: 224}, {0: "03"}
        )

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
        response = self.make_category_request(
            data, meeting_id, is_update, request_with_numbers
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
        self.make_conditional_number_assertions_for_category_test(
            rows, is_update, request_with_numbers, is_set_number, {0: 224}, {0: "03"}
        )

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
        response = self.make_category_request(
            data, meeting_id, is_update, request_with_numbers
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
        self.make_conditional_number_assertions_for_category_test(
            rows,
            is_update,
            request_with_numbers,
            is_set_number,
            {0: 224},
            {0: "AMNDMNT01"},
        )

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

    def test_json_upload_with_similar_category_in_different_meeting(self) -> None:
        self.set_up_models(
            {
                42: self.get_category_extended_base_meeting_setting(223, 2223),
                43: self.get_category_extended_base_meeting_setting(334, 3334),
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
        response = self.make_category_request(data, 42, False, False)
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.DONE
        assert response.json["results"][0][0]["rows"][0]["data"]["category_name"] == {
            "id": 2224,
            "info": ImportState.DONE,
            "value": "Amendment category",
        }

    # -------------------- Test with users --------------------

    def generate_user_setting(
        self,
        username: str,
        meeting_settings: Dict[int, SetupMeetingSetting],
        meeting_ids: List[int] = [],
        submitted_motion_ids: List[int] = [],
        supported_motion_ids: List[int] = [],
    ) -> SetupUserSetting:
        user_data: SetupUserSetting = {"username": username}
        meeting_ids = [
            meeting_id for meeting_id in meeting_ids if meeting_settings.get(meeting_id)
        ]
        if len(meeting_ids) == 0:
            return user_data
        user_data["meeting_ids"] = meeting_ids
        motion_ids: List[int] = []
        for meeting_id in meeting_ids:
            meeting_setting = meeting_settings[meeting_id]
            motion_ids.extend(meeting_setting.get("motions", {}).keys())
            for motion_id in meeting_setting.get("motions", {}):
                motion_ids.extend(
                    meeting_setting.get("motions", {})[motion_id]
                    .get("amendments", {})
                    .keys()
                )
        submitted_motion_ids = [
            motion_id for motion_id in motion_ids if motion_id in submitted_motion_ids
        ]
        supported_motion_ids = [
            motion_id for motion_id in motion_ids if motion_id in supported_motion_ids
        ]
        if len(submitted_motion_ids):
            user_data["submitted_motion_ids"] = submitted_motion_ids
        if len(supported_motion_ids):
            user_data["supported_motion_ids"] = supported_motion_ids
        return user_data

    def get_base_user_and_meeting_settings(
        self,
        base_meeting_id: int = 42,
        base_motion_id: int = 222,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> Tuple[Dict[int, SetupMeetingSetting], List[SetupUserSetting]]:
        meeting_settings = {
            base_meeting_id: self.get_base_meeting_setting(
                base_motion_id, is_reason_required, is_set_number
            ),
            (base_meeting_id + 1): self.get_base_meeting_setting(
                base_motion_id + 100, is_reason_required, is_set_number
            ),
        }
        user_settings = [
            # One non-meeting user
            self.generate_user_setting("nonMeeting", meeting_settings),
            # some first-meeting users
            self.generate_user_setting(
                "firstMeeting", meeting_settings, [base_meeting_id]
            ),
            self.generate_user_setting(
                "firstMeetingSubmitter",
                meeting_settings,
                [base_meeting_id],
                [base_motion_id],
            ),
            self.generate_user_setting(
                "firstMeetingSupporter",
                meeting_settings,
                [base_meeting_id],
                supported_motion_ids=[base_motion_id + 3],
            ),
            self.generate_user_setting(
                "firstMeetingBoth",
                meeting_settings,
                [base_meeting_id],
                [base_motion_id + 1],
                [base_motion_id + 2],
            ),
            # some second-meeting users
            self.generate_user_setting(
                "secondMeeting", meeting_settings, [base_meeting_id + 1]
            ),
            self.generate_user_setting(
                "secondMeetingSubmitter",
                meeting_settings,
                [base_meeting_id + 1],
                [base_motion_id + 100, base_motion_id + 101],
            ),
            self.generate_user_setting(
                "secondMeetingSupporter",
                meeting_settings,
                [base_meeting_id + 1],
                supported_motion_ids=[base_motion_id + 100, base_motion_id + 101],
            ),
            self.generate_user_setting(
                "secondMeetingBoth",
                meeting_settings,
                [base_meeting_id + 1],
                [base_motion_id + 101, base_motion_id + 102],
                supported_motion_ids=[base_motion_id + 100, base_motion_id + 103],
            ),
            # some multi-meeting users
            self.generate_user_setting(
                "multiMeeting",
                meeting_settings,
                [base_meeting_id, base_meeting_id + 1],
            ),
            self.generate_user_setting(
                "multiMeetingSubmitter",
                meeting_settings,
                [base_meeting_id, base_meeting_id + 1],
                [base_motion_id + 3],
            ),
            self.generate_user_setting(
                "multiMeetingSupporter",
                meeting_settings,
                [base_meeting_id, base_meeting_id + 1],
                supported_motion_ids=[base_motion_id + 103],
            ),
            self.generate_user_setting(
                "multiMeetingBoth",
                meeting_settings,
                [base_meeting_id, base_meeting_id + 1],
                [base_motion_id + 3, base_motion_id + 100],
                [base_motion_id + 101, base_motion_id + 102],
            ),
        ]
        return (meeting_settings, user_settings)

    # TODO add verbose checking, allow for other numbers?
    def assert_with_submitters(
        self,
        usernames: Optional[List[str]] = None,
        username: Optional[str] = None,
        in_first_meeting: bool = True,
        is_update: bool = False,
    ) -> None:
        settings = self.get_base_user_and_meeting_settings()
        model_data = self.set_up_models(*settings)
        payload = {
            "title": "test",
            "text": "my",
            "submitters_username": usernames or username or "unknown",
        }
        if is_update:
            payload["number"] = "NUM01"
        meeting_id = 42 if in_first_meeting else 43
        response = self.request(
            "motion.json_upload",
            {
                "data": [payload],
                "meeting_id": meeting_id,
            },
        )
        has_unknown_user = not (usernames or username)
        usernames = usernames or ([username] if username else [])
        collections_and_ids = {fqid: fqid.split("/") for fqid in model_data}
        usernames_to_user_ids = {
            username: int(collections_and_ids[fqid][1])
            for username in usernames
            for fqid in model_data
            if (collections_and_ids[fqid][0] == "user")
            and (username == model_data[fqid]["username"])
        }
        # foreign_meeting_users = [
        #     username
        #     for username in usernames
        #     if username not in usernames_to_meeting_user_ids.keys()
        # ]
        expected_user_objects = []
        if has_unknown_user:
            expected_user_objects = [
                {"info": ImportState.WARNING, "value": "unknown"},
                {"id": 1, "info": ImportState.GENERATED, "value": "admin"},
            ]
        else:
            expected_user_objects = [
                {"info": ImportState.DONE, "id": user_id, "value": name}
                for (name, user_id) in usernames_to_user_ids.items()
            ]  # TODO Expand with foreign meeting users
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == (
            ImportState.WARNING if has_unknown_user else ImportState.DONE
        )
        assert len(response.json["results"][0][0]["rows"]) == 1
        data = {
            "meeting_id": 42,
            "title": {"value": "test", "info": ImportState.DONE},
            "text": {"value": "<p>my</p>", "info": ImportState.DONE},
            "submitters_username": expected_user_objects,
        }
        row = response.json["results"][0][0]["rows"][0]
        assert row["state"] == (ImportState.DONE if is_update else ImportState.NEW)
        assert row["messages"] == (
            ["Submitters: Could not find the user for at least one username"]
            if has_unknown_user
            else []
        )
        for key in data:
            assert row["data"].get(key) == data[key]

    def test_json_upload_create_with_unknown_submitter(self) -> None:
        self.assert_with_submitters()

    def test_json_upload_create_with_simple_submitter(self) -> None:
        self.assert_with_submitters(username="firstMeeting")

    def test_json_upload_create_with_simple_submitter_in_list(self) -> None:
        self.assert_with_submitters(usernames=["firstMeeting"])

    def test_json_upload_update_with_unknown_submitter(self) -> None:
        self.assert_with_submitters(is_update=True)

    def test_json_upload_update_with_simple_submitter(self) -> None:
        self.assert_with_submitters(username="firstMeeting", is_update=True)

    def test_json_upload_update_with_simple_submitter_in_list(self) -> None:
        self.assert_with_submitters(usernames=["firstMeeting"], is_update=True)

    # TODO: More tests with assert_with_submitters