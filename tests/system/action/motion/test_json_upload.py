from typing import Any, TypedDict, cast

from typing_extensions import NotRequired

from openslides_backend.action.mixins.import_mixins import ImportState
from tests.system.action.base import BaseActionTestCase


class SetupUserSetting(TypedDict):
    username: str
    meeting_ids: NotRequired[list[int]]
    submitted_motion_ids: NotRequired[list[int]]
    supported_motion_ids: NotRequired[list[int]]
    no_group: NotRequired[bool]


class SetupCommonMotionSetting(TypedDict, total=False):
    has_number: bool
    category_id: int
    tag_ids: list[int]
    block_id: int


class SetupAmendmentSetting(TypedDict):
    base: SetupCommonMotionSetting
    fields: list[str]


class SetupMotionSetting(TypedDict):
    base: SetupCommonMotionSetting
    amendments: NotRequired[dict[int, SetupAmendmentSetting]]


class SetupWorkflowSetting(TypedDict):
    first_state_fields: list[str]


class SetupCategorySetting(TypedDict):
    name: str
    prefix: NotRequired[str]


class SetupMeetingSetting(TypedDict):
    fields: list[str]
    motions: NotRequired[dict[int, SetupMotionSetting]]
    categories: NotRequired[dict[int, SetupCategorySetting]]
    workflow: NotRequired[SetupWorkflowSetting]
    tags: NotRequired[dict[int, str]]
    blocks: NotRequired[dict[int, str]]
    set_number: NotRequired[bool]


class UsernameTestData(TypedDict, total=False):
    submitters: list[str] | str | None
    supporters: list[str] | str | None


class UsernameTestAssertionData(TypedDict):
    usernames: list[str]
    own_meeting_usernames: list[str]
    own_meeting_groupless_usernames: list[str]
    unknown_user_present: bool
    usernames_to_user_ids: dict[str, int]


UsernameTestExpectationInfo = dict[str, UsernameTestAssertionData]


class MotionImportTestMixin(BaseActionTestCase):
    def set_up_models(
        self,
        meetings: dict[int, SetupMeetingSetting],
        users: list[SetupUserSetting] | None = None,
    ) -> dict[str, Any]:
        model_data: dict[str, Any] = {}
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
                **self._build_base_model_data_from_prototype(
                    meeting_prototype, setting["fields"]
                ),
                "name": "test meeting" + str(meeting_id),
                "group_ids": [meeting_id * 10],
            }
            model_data["group/" + str(meeting_id * 10)] = {
                "meeting_id": meeting_id,
                "name": "test",
            }
            self._set_up_workflow(
                model_data,
                meeting_data,
                meeting_id,
                next_ids,
                setting.get("set_number", False),
            )
            if category_settings := setting.get("categories"):
                self._set_up_categories(
                    model_data, meeting_id, meeting_data, category_settings
                )
            if tag_settings := setting.get("tags"):
                meeting_data["tag_ids"] = list(tag_settings.keys())
                for tag_id in tag_settings:
                    model_data[f"tag/{tag_id}"] = {
                        "name": tag_settings[tag_id],
                        "meeting_id": meeting_id,
                        "tagged_ids": [],
                    }
            if block_settings := setting.get("blocks"):
                meeting_data["motion_block_ids"] = list(block_settings.keys())
                for block_id in block_settings:
                    model_data[f"motion_block/{block_id}"] = {
                        "title": block_settings[block_id],
                        "meeting_id": meeting_id,
                        "motion_ids": [],
                    }
            if motion_settings := setting.get("motions"):
                self._set_up_motions(
                    model_data, meeting_id, meeting_data, motion_settings
                )
            model_data["meeting/" + str(meeting_id)] = meeting_data
        if users:
            for idx, user_setting in enumerate(users):
                self._set_up_user(idx + 2, user_setting, model_data)
        self.set_models(model_data)
        return model_data

    def _build_base_model_data_from_prototype(
        self, prototype: dict[str, Any], fields: list[str]
    ) -> dict[str, Any]:
        data = {}
        for field in fields:
            if prototype.get(field):
                data[field] = prototype[field]
        return data

    def _set_up_user(
        self,
        user_id: int,
        setting: SetupUserSetting,
        model_data: dict[str, dict[str, Any]],
    ) -> None:
        user_data: dict[str, Any] = {"username": setting["username"]}
        if setting.get("meeting_ids") and not setting.get("no_group"):
            user_data["meeting_ids"] = setting.get("meeting_ids")
        next_meeting_user_id = user_id * 100
        meeting_ids = setting.get("meeting_ids", [])
        for meeting_id in meeting_ids:
            if meeting := model_data.get("meeting/" + str(meeting_id)):
                next_motion_submitter_id = next_meeting_user_id * 100
                user_data["meeting_user_ids"] = [
                    *user_data.get("meeting_user_ids", []),
                    next_meeting_user_id,
                ]
                meeting_user_data: dict[str, Any] = {
                    "user_id": user_id,
                    "meeting_id": meeting_id,
                }
                meeting["meeting_user_ids"] = [
                    *meeting.get("meeting_user_ids", []),
                    next_meeting_user_id,
                ]
                if not setting.get("no_group"):
                    meeting_user_data["group_ids"] = [meeting_id * 10]
                    model_data["group/" + str(meeting_id * 10)]["meeting_user_ids"] = (
                        meeting["meeting_user_ids"]
                    )
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
                            "weight": len(motion.get("submitter_ids", [])),
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
                model_data["meeting_user/" + str(next_meeting_user_id)] = (
                    meeting_user_data
                )
                next_meeting_user_id += 1
        model_data["user/" + str(user_id)] = user_data

    def _set_up_categories(
        self,
        model_data: dict[str, Any],
        meeting_id: int,
        meeting_data: dict[str, Any],
        category_settings: dict[int, SetupCategorySetting],
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

    def _set_up_motions(
        self,
        model_data: dict[str, Any],
        meeting_id: int,
        meeting_data: dict[str, Any],
        motion_settings: dict[int, SetupMotionSetting],
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
            self._set_up_extras_for_motion(
                model_data, motion_id, motion_setting, motion_data
            )
            if amendment_settings := motion_setting.get("amendments"):
                amendment_ids = [id_ for id_ in amendment_settings]
                motion_ids.extend(amendment_ids)
                for amendment_id in amendment_ids:
                    amendment_setting = amendment_settings[amendment_id]
                    amendment_data = {
                        **self._build_base_model_data_from_prototype(
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
                    self._set_up_extras_for_motion(
                        model_data, amendment_id, amendment_setting, amendment_data
                    )
                    model_data["motion/" + str(amendment_id)] = amendment_data
            model_data["motion/" + str(motion_id)] = motion_data

    def _set_up_extras_for_motion(
        self,
        model_data: dict[str, dict[str, Any]],
        motion_id: int,
        motion_setting: Any,
        motion_data: dict[str, Any],
    ) -> None:
        base = cast(SetupCommonMotionSetting, motion_setting["base"])
        if category_id := base.get("category_id"):
            motion_data["category_id"] = category_id
            model_data["motion_category/" + str(category_id)]["motion_ids"].append(
                motion_id
            )
        if tag_ids := base.get("tag_ids"):
            motion_data["tag_ids"] = tag_ids
            for tag_id in tag_ids:
                model_data["tag/" + str(tag_id)]["tagged_ids"].append(
                    f"motion/{motion_id}"
                )
        if block_id := base.get("block_id"):
            motion_data["block_id"] = block_id
            model_data["motion_block/" + str(block_id)]["motion_ids"].append(motion_id)

    def _set_up_workflow(
        self,
        model_data: dict[str, Any],
        meeting_data: dict[str, Any],
        meeting_id: int,
        next_ids: dict[str, int],
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
        state_data: dict[str, Any] = {
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
                (base_motion_id + 2): (base_category_id + 1),
                (base_motion_id + 3): (base_category_id + 3),
                (base_motion_id + 4): base_category_id,
            },
        )

    def get_base_user_and_meeting_settings(
        self,
        base_meeting_id: int = 42,
        base_motion_id: int = 222,
        is_reason_required: bool = False,
        is_set_number: bool = False,
    ) -> tuple[dict[int, SetupMeetingSetting], list[SetupUserSetting]]:
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
            self._generate_user_setting("noMeeting", meeting_settings),
            # some first-meeting users
            self._generate_user_setting(
                "firstMeeting", meeting_settings, [base_meeting_id]
            ),
            self._generate_user_setting(
                "firstMeetingSubmitter",
                meeting_settings,
                [base_meeting_id],
                [base_motion_id],
            ),
            self._generate_user_setting(
                "firstMeetingGrouplessSubmitter",
                meeting_settings,
                [base_meeting_id],
                [base_motion_id],
                no_group=True,
            ),
            self._generate_user_setting(
                "firstMeetingSupporter",
                meeting_settings,
                [base_meeting_id],
                supported_motion_ids=[base_motion_id + 3],
            ),
            self._generate_user_setting(
                "firstMeetingBoth",
                meeting_settings,
                [base_meeting_id],
                [base_motion_id + 1],
                [base_motion_id + 2],
            ),
            # some second-meeting users
            self._generate_user_setting(
                "secondMeeting", meeting_settings, [base_meeting_id + 1]
            ),
            self._generate_user_setting(
                "secondMeetingSubmitter",
                meeting_settings,
                [base_meeting_id + 1],
                [base_motion_id + 100, base_motion_id + 101],
            ),
            self._generate_user_setting(
                "secondMeetingSupporter",
                meeting_settings,
                [base_meeting_id + 1],
                supported_motion_ids=[base_motion_id + 100, base_motion_id + 101],
            ),
            self._generate_user_setting(
                "secondMeetingBoth",
                meeting_settings,
                [base_meeting_id + 1],
                [base_motion_id + 101, base_motion_id + 102],
                supported_motion_ids=[base_motion_id + 100, base_motion_id + 103],
            ),
            # some multi-meeting users
            self._generate_user_setting(
                "multiMeeting",
                meeting_settings,
                [base_meeting_id, base_meeting_id + 1],
            ),
            self._generate_user_setting(
                "multiMeetingSubmitter",
                meeting_settings,
                [base_meeting_id, base_meeting_id + 1],
                [base_motion_id + 3],
            ),
            self._generate_user_setting(
                "multiMeetingSupporter",
                meeting_settings,
                [base_meeting_id, base_meeting_id + 1],
                supported_motion_ids=[base_motion_id + 103],
            ),
            self._generate_user_setting(
                "multiMeetingBoth",
                meeting_settings,
                [base_meeting_id, base_meeting_id + 1],
                [base_motion_id + 3, base_motion_id + 100],
                [base_motion_id + 101, base_motion_id + 102],
            ),
        ]
        return (meeting_settings, user_settings)

    def get_base_meeting_setting_with_tags(
        self, base_motion_id: int, base_tag_id: int, extra_tags: list[str] = []
    ) -> SetupMeetingSetting:
        return self.extend_meeting_setting_with_tags(
            self.get_base_meeting_setting(base_motion_id, False, False),
            base_tag_id,
            extra_tags,
        )

    def extend_meeting_setting_with_tags(
        self,
        setting: SetupMeetingSetting,
        base_tag_id: int,
        extra_tags: list[str] = [],
        motion_to_tag_ids: dict[int, list[int]] = {},
    ) -> SetupMeetingSetting:
        setting["tags"] = {
            base_tag_id: "Tag-liatelle",
            (base_tag_id + 1): "Tag-you're-it",
            (base_tag_id + 2): "Price tag",
            (base_tag_id + 3): "Tag-ether",
            (base_tag_id + 4): "Tag-ether",
            **{
                base_tag_id + 5 + index: extra_tags[index]
                for index in range(len(extra_tags))
            },
        }
        for motion_id in setting.get("motions", {}):
            motion = setting.get("motions", {})[motion_id]
            self._add_tag_ids(motion_id, motion, motion_to_tag_ids)
            for amendment_id in motion.get("amendments", {}):
                self._add_tag_ids(
                    amendment_id,
                    motion.get("amendments", {})[amendment_id],
                    motion_to_tag_ids,
                )
        return setting

    def get_base_meeting_setting_with_blocks(
        self, base_motion_id: int, base_block_id: int, extra_blocks: list[str] = []
    ) -> SetupMeetingSetting:
        return self.extend_meeting_setting_with_blocks(
            self.get_base_meeting_setting(base_motion_id, False, False),
            base_block_id,
            extra_blocks,
        )

    def extend_meeting_setting_with_blocks(
        self,
        setting: SetupMeetingSetting,
        base_block_id: int,
        extra_blocks: list[str] = [],
        motion_to_block_ids: dict[int, int] = {},
    ) -> SetupMeetingSetting:
        setting["blocks"] = {
            base_block_id: "Blockolade",
            (base_block_id + 1): "Blockodile",
            (base_block_id + 2): "Blockoli",
            (base_block_id + 3): "Block chain",
            (base_block_id + 4): "Block chain",
            **{
                base_block_id + 5 + index: extra_blocks[index]
                for index in range(len(extra_blocks))
            },
        }
        for motion_id in setting.get("motions", {}):
            motion = setting.get("motions", {})[motion_id]
            self._add_block_id(motion_id, motion, motion_to_block_ids)
            for amendment_id in motion.get("amendments", {}):
                self._add_block_id(
                    amendment_id,
                    motion.get("amendments", {})[amendment_id],
                    motion_to_block_ids,
                )
        return setting

    def extend_meeting_setting_with_categories(
        self,
        setting: SetupMeetingSetting,
        categories: dict[int, SetupCategorySetting],
        motion_to_category_ids: dict[int, int],
    ) -> SetupMeetingSetting:
        setting["categories"] = categories
        for motion_id in setting.get("motions", {}):
            motion = setting.get("motions", {})[motion_id]
            self._add_category_id(motion_id, motion, motion_to_category_ids)
            for amendment_id in motion.get("amendments", {}):
                self._add_category_id(
                    amendment_id,
                    motion.get("amendments", {})[amendment_id],
                    motion_to_category_ids,
                )
        return setting

    def _add_category_id(
        self,
        motion_id: int,
        motion: Any,
        motion_to_category_ids: dict[int, int],
    ) -> None:
        if motion_to_category_ids.get(motion_id):
            motion["base"]["category_id"] = motion_to_category_ids[motion_id]

    def _add_tag_ids(
        self,
        motion_id: int,
        motion: Any,
        motion_to_tag_ids: dict[int, list[int]],
    ) -> None:
        if motion_to_tag_ids.get(motion_id):
            motion["base"]["tag_ids"] = motion_to_tag_ids[motion_id]

    def _add_block_id(
        self,
        motion_id: int,
        motion: Any,
        motion_to_block_ids: dict[int, int],
    ) -> None:
        if motion_to_block_ids.get(motion_id):
            motion["base"]["block_id"] = motion_to_block_ids[motion_id]

    def _generate_user_setting(
        self,
        username: str,
        meeting_settings: dict[int, SetupMeetingSetting],
        meeting_ids: list[int] = [],
        submitted_motion_ids: list[int] = [],
        supported_motion_ids: list[int] = [],
        no_group: bool = False,
    ) -> SetupUserSetting:
        user_data: SetupUserSetting = {"username": username, "no_group": no_group}
        meeting_ids = [
            meeting_id for meeting_id in meeting_ids if meeting_settings.get(meeting_id)
        ]
        if len(meeting_ids) == 0:
            return user_data
        user_data["meeting_ids"] = meeting_ids
        motion_ids: list[int] = []
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


class MotionJsonUpload(MotionImportTestMixin):
    # -------------------------------------------------------
    # --------------------[ Basic tests ]--------------------
    # -------------------------------------------------------

    def test_json_upload_empty_data(self) -> None:
        response = self.request(
            "motion.json_upload",
            {"data": [], "meeting_id": 42},
        )
        self.assert_status_code(response, 400)
        assert "data.data must contain at least 1 items" in response.json["message"]

    def test_json_upload_amendment(self) -> None:
        meeting_id = 42
        self.set_up_models({meeting_id: self.get_base_meeting_setting(200)})
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my", "motion_amendment": "1"}],
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 1
        assert response.json["results"][0][0]["state"] == ImportState.WARNING
        data = {
            "meeting_id": meeting_id,
            "title": {"value": "test", "info": ImportState.DONE},
            "text": {"value": "<p>my</p>", "info": ImportState.DONE},
            "motion_amendment": {"value": True, "info": ImportState.WARNING},
            "submitters_username": [{"id": 1, "info": "generated", "value": "admin"}],
            "number": {"info": ImportState.DONE, "value": ""},
            "reason": {"info": ImportState.DONE, "value": ""},
            "category_name": {"info": ImportState.DONE, "value": ""},
            "block": {"info": ImportState.DONE, "value": ""},
            "tags": [],
            "supporters_username": [],
        }
        expected = {
            "state": ImportState.NEW,
            "messages": ["Amendments cannot be correctly imported"],
            "data": data,
        }
        assert response.json["results"][0][0]["rows"][0] == expected

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
            "number": {"info": ImportState.DONE, "value": ""},
            "category_name": {"info": ImportState.DONE, "value": ""},
            "block": {"info": ImportState.DONE, "value": ""},
            "tags": [],
            "supporters_username": [],
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
                "category_name": {"value": "", "info": "done"},
                "block": {"value": "", "info": "done"},
                "supporters_username": [],
                "tags": [],
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
            "number": {"info": ImportState.DONE, "value": ""},
            "category_name": {"info": ImportState.DONE, "value": ""},
            "block": {"info": ImportState.DONE, "value": ""},
            "tags": [],
            "supporters_username": [],
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
            "number": {"info": ImportState.DONE, "value": ""},
            "category_name": {"info": ImportState.DONE, "value": ""},
            "block": {"info": ImportState.DONE, "value": ""},
            "tags": [],
            "supporters_username": [],
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
                "category_name": {"value": "", "info": "done"},
                "block": {"value": "", "info": "done"},
                "supporters_username": [],
                "tags": [],
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

    def test_json_upload_update_missing_title(self) -> None:
        self.set_up_models({42: self.get_base_meeting_setting(223)})
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"text": "my", "reason": "stuff", "number": "NUM01"}],
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

    def test_json_upload_update_missing_text(self) -> None:
        self.set_up_models({42: self.get_base_meeting_setting(223)})
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "reason": "stuff", "number": "NUM01"}],
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
                "number": {"info": ImportState.DONE, "value": ""},
                "reason": {"info": ImportState.DONE, "value": ""},
                "category_name": {"info": ImportState.DONE, "value": ""},
                "block": {"info": ImportState.DONE, "value": ""},
                "tags": [],
                "supporters_username": [],
            },
        }

    def test_json_upload_create_fields_empty(self) -> None:
        self.set_up_models({42: self.get_base_meeting_setting(223)})
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "title": "test",
                        "text": "<p>my</p>",
                        "submitters_username": "",
                        "number": "",
                        "reason": "",
                        "category_name": "",
                        "block": "",
                        "tags": "",
                        "supporters_username": "",
                    }
                ],
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
                "number": {"info": ImportState.DONE, "value": ""},
                "reason": {"info": ImportState.DONE, "value": ""},
                "category_name": {"info": ImportState.DONE, "value": ""},
                "block": {"info": ImportState.DONE, "value": ""},
                "tags": [],
                "supporters_username": [],
            },
        }

    def test_json_upload_update_fields_empty(self) -> None:
        self.set_up_models({42: self.get_base_meeting_setting(223)})
        response = self.request(
            "motion.json_upload",
            {
                "data": [
                    {
                        "title": "test",
                        "text": "<p>my</p>",
                        "submitters_username": "",
                        "number": "NUM01",
                        "reason": "",
                        "category_name": "",
                        "block": "",
                        "tags": "",
                        "supporters_username": "",
                    }
                ],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["rows"][0] == {
            "state": ImportState.DONE,
            "messages": [],
            "data": {
                "meeting_id": 42,
                "id": 224,
                "title": {"value": "test", "info": ImportState.DONE},
                "text": {"value": "<p>my</p>", "info": ImportState.DONE},
                "submitters_username": [
                    {"id": 1, "info": "generated", "value": "admin"}
                ],
                "number": {"info": ImportState.DONE, "value": "NUM01", "id": 224},
                "reason": {"info": ImportState.DONE, "value": ""},
                "category_name": {"info": ImportState.DONE, "value": ""},
                "block": {"info": ImportState.DONE, "value": ""},
                "tags": [],
                "supporters_username": [],
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

    def test_json_upload_update_missing_reason_although_required(self) -> None:
        self.set_up_models(
            {42: self.get_base_meeting_setting(223, is_reason_required=True)}
        )
        response = self.request(
            "motion.json_upload",
            {
                "data": [{"title": "test", "text": "my", "number": "NUM01"}],
                "meeting_id": 42,
            },
        )
        self.assert_status_code(response, 200)
        assert response.json["results"][0][0]["state"] == ImportState.ERROR
        assert (
            "Error: Reason is required to update."
            in response.json["results"][0][0]["rows"][0]["messages"]
        )
        assert response.json["results"][0][0]["rows"][0]["data"]["reason"] == {
            "value": "",
            "info": ImportState.ERROR,
        }

    def assert_custom_number_create(
        self, is_set_number: bool = False
    ) -> list[dict[str, Any]]:
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
                "category_name": {"info": ImportState.DONE, "value": ""},
                "block": {"info": ImportState.DONE, "value": ""},
                "tags": [],
                "supporters_username": [],
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
                "category_name": {"info": ImportState.DONE, "value": ""},
                "block": {"info": ImportState.DONE, "value": ""},
                "tags": [],
                "supporters_username": [],
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

    # -------------------------------------------------------
    # ---------------[ Test with categories ]----------------
    # -------------------------------------------------------

    def make_conditional_number_assertions_for_category_test(
        self,
        rows: list[dict[str, Any]],
        is_update: bool = False,
        request_with_numbers: bool = False,
        is_set_number: bool = False,
        ids_for_row_indices: dict[int, int | None] = {},
        generated_numbers_for_row_indices: dict[int, str | None] = {},
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
                assert rows[i]["data"].get("number") == {"value": "", "info": "done"}

    def make_category_request(
        self,
        data: list[dict[str, Any]],
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
        data: list[dict[str, Any]] = list(
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
        data: list[dict[str, Any]] = list(
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
            rows, is_update, request_with_numbers, is_set_number, {0: 224}, {0: "01"}
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
        data: list[dict[str, Any]] = list(
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
            rows, is_update, request_with_numbers, is_set_number, {0: 224}, {0: "01"}
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
        data: list[dict[str, Any]] = list(
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
            rows, is_update, request_with_numbers, is_set_number, {0: 224}, {0: "01"}
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
        data: list[dict[str, Any]] = list(
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
            rows, is_update, request_with_numbers, is_set_number, {0: 224}, {0: "01"}
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
        data: list[dict[str, Any]] = list(
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
            {0: "AMNDMNT02"},
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
        data: list[dict[str, Any]] = list(
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

    # -------------------------------------------------------
    # ------------------[ Test with users ]------------------
    # -------------------------------------------------------

    def get_user_request_response_and_model_data_in_first_meeting(
        self,
        meeting_id: int,
        username_data: UsernameTestData,
        add_unknown_user: bool = False,
        is_update: bool = False,
        multiple: bool = False,
    ) -> tuple[Any, dict[str, Any]]:
        rows = 2 if multiple else 1
        model_data = self.set_up_models(*self.get_base_user_and_meeting_settings())
        payloads = []
        username_dict = cast(dict, username_data)
        for i in range(rows):
            payload: dict[str, Any] = {"title": "test", "text": "my"}
            for key in username_dict:
                uname_data = username_dict[key]
                (username, usernames) = (
                    (uname_data, None)
                    if isinstance(uname_data, str)
                    else (None, cast(list[str], uname_data))
                )
                if add_unknown_user:
                    payload[f"{key}_username"] = [
                        *(usernames or ([username] if username else [])),
                        "unknown",
                    ]
                else:
                    payload[f"{key}_username"] = usernames or username or "unknown"
            if is_update:
                payload["number"] = "NUM0" + str(i + 1)
            payloads.append(payload)
        response = self.request(
            "motion.json_upload",
            {
                "data": payloads,
                "meeting_id": meeting_id,
            },
        )
        return (response, model_data)

    def get_own_meeting_users_groupless_users_and_user_id_dict(
        self, usernames: list[str], meeting_id: int, model_data: dict[str, Any]
    ) -> tuple[list[str], list[str], dict[str, int]]:
        collections_and_ids = {fqid: fqid.split("/") for fqid in model_data}
        usernames_to_user_ids = {
            username: int(collections_and_ids[fqid][1])
            for username in usernames
            for fqid in model_data
            if (collections_and_ids[fqid][0] == "user")
            and (username == model_data[fqid]["username"])
        }
        own_meeting_usernames = [
            username
            for username in usernames
            for fqid in model_data
            for meeting_user_id in model_data[fqid].get("meeting_user_ids", [])
            if model_data["meeting_user/" + str(meeting_user_id)].get("meeting_id")
            == meeting_id
            and collections_and_ids[fqid][0] == "user"
            and model_data[fqid]["username"] == username
        ]
        own_meeting_groupless_usernames = [
            username
            for username in own_meeting_usernames
            for fqid in model_data
            if len(model_data[fqid].get("meeting_user_ids", []))
            and (
                not model_data[
                    "meeting_user/"
                    + str(model_data[fqid].get("meeting_user_ids", [0])[0])
                ].get("group_ids")
            )
            and collections_and_ids[fqid][0] == "user"
            and model_data[fqid]["username"] == username
        ]
        return (
            own_meeting_usernames,
            own_meeting_groupless_usernames,
            usernames_to_user_ids,
        )

    def get_expected_user_objects(
        self,
        user_data: UsernameTestAssertionData,
        add_default_if_necessary: bool = False,
    ) -> list[dict[str, Any]]:
        expected_user_objects: list[dict[str, Any]] = [
            (
                {"info": ImportState.WARNING, "value": name}
                if (
                    name not in user_data["own_meeting_usernames"]
                    or name in user_data["own_meeting_groupless_usernames"]
                )
                else {
                    "info": ImportState.DONE,
                    "id": user_data["usernames_to_user_ids"][name],
                    "value": name,
                }
            )
            for name in user_data["usernames"]
        ]
        if user_data["unknown_user_present"]:
            expected_user_objects.append(
                {"info": ImportState.WARNING, "value": "unknown"}
            )
        if (
            add_default_if_necessary
            and len(
                [
                    user
                    for user in expected_user_objects
                    if user.get("info") == ImportState.DONE
                ]
            )
            == 0
        ):
            expected_user_objects.append(
                {"id": 1, "info": ImportState.GENERATED, "value": "admin"}
            )
        return expected_user_objects

    def make_simple_user_assertions_in_first_meeting(
        self,
        response: Any,
        user_data: UsernameTestExpectationInfo,
        is_update: bool = False,
        multiple: bool = False,
    ) -> None:
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == (2 if multiple else 1)
        has_warning = False
        expected_data: dict[str, Any] = {}
        for key in user_data:
            expected_data.update(
                {
                    f"{key}s_username": self.get_expected_user_objects(
                        user_data[key], key == "submitter"
                    )
                }
            )
        for row in response.json["results"][0][0]["rows"]:
            expected_messages: list[str] = []
            for usertype in user_data:
                user_date = user_data[usertype]
                has_unknown_users = (
                    (
                        len(user_date["own_meeting_usernames"])
                        != len(user_date["usernames"])
                    )
                    or user_date["unknown_user_present"]
                    or len(user_date["own_meeting_groupless_usernames"]) != 0
                )
                has_warning = has_warning or has_unknown_users
                assert row["state"] == (
                    ImportState.DONE if is_update else ImportState.NEW
                )

                if has_unknown_users:
                    expected_messages.append(
                        f"Could not find at least one {usertype}: "
                    )
                for key in expected_data:
                    assert row["data"].get(key) == expected_data[key]
            assert len(row["messages"]) == len(expected_messages)
            for message in expected_messages:
                assert any(
                    [message in actual_message for actual_message in row["messages"]]
                )
        assert response.json["results"][0][0]["state"] == (
            ImportState.WARNING if has_warning else ImportState.DONE
        )

    def assert_with_submitters_in_first_meeting(
        self,
        username_data: list[str] | str | None = None,
        add_unknown_user: bool = False,
        is_update: bool = False,
        multiple: bool = False,
    ) -> None:
        meeting_id = 42
        (
            response,
            model_data,
        ) = self.get_user_request_response_and_model_data_in_first_meeting(
            meeting_id,
            {"submitters": username_data},
            add_unknown_user,
            is_update,
            multiple,
        )
        unknown_user_present = add_unknown_user or not username_data
        usernames = (
            [username_data]
            if isinstance(username_data, str)
            else cast(list[str], username_data) or []
        )
        (
            own_meeting_usernames,
            own_meeting_groupless_usernames,
            usernames_to_user_ids,
        ) = self.get_own_meeting_users_groupless_users_and_user_id_dict(
            usernames, meeting_id, model_data
        )
        user_data: UsernameTestAssertionData = {
            "usernames": usernames,
            "own_meeting_usernames": own_meeting_usernames,
            "unknown_user_present": unknown_user_present,
            "usernames_to_user_ids": usernames_to_user_ids,
            "own_meeting_groupless_usernames": own_meeting_groupless_usernames,
        }
        self.make_simple_user_assertions_in_first_meeting(
            response,
            {"submitter": user_data},
            is_update,
            multiple,
        )

    def test_json_upload_create_with_unknown_submitter(self) -> None:
        self.assert_with_submitters_in_first_meeting()

    def test_json_upload_update_with_unknown_submitter(self) -> None:
        self.assert_with_submitters_in_first_meeting(is_update=True)

    def test_json_upload_create_with_simple_submitter(self) -> None:
        self.assert_with_submitters_in_first_meeting("firstMeeting")

    def test_json_upload_update_with_simple_submitter(self) -> None:
        self.assert_with_submitters_in_first_meeting("firstMeeting", is_update=True)

    def test_json_upload_create_with_groupless_submitter(self) -> None:
        self.assert_with_submitters_in_first_meeting("firstMeetingGrouplessSubmitter")

    def test_json_upload_update_with_groupless_submitter(self) -> None:
        self.assert_with_submitters_in_first_meeting(
            "firstMeetingGrouplessSubmitter", is_update=True
        )

    def test_json_upload_create_with_simple_submitter_in_list(self) -> None:
        self.assert_with_submitters_in_first_meeting(["firstMeeting"])

    def test_json_upload_update_with_simple_submitter_in_list(self) -> None:
        self.assert_with_submitters_in_first_meeting(["firstMeeting"], is_update=True)

    def test_json_upload_create_with_two_submitters_in_list(self) -> None:
        self.assert_with_submitters_in_first_meeting(
            ["firstMeeting", "firstMeetingBoth"]
        )

    def test_json_upload_update_with_two_submitters_in_list(self) -> None:
        self.assert_with_submitters_in_first_meeting(
            ["firstMeeting", "firstMeetingBoth"], is_update=True
        )

    def test_json_upload_create_with_unknown_submitter_in_list(self) -> None:
        self.assert_with_submitters_in_first_meeting(
            ["firstMeeting"], add_unknown_user=True
        )

    def test_json_upload_update_with_unknown_submitter_in_list(self) -> None:
        self.assert_with_submitters_in_first_meeting(
            ["firstMeeting"], add_unknown_user=True, is_update=True
        )

    def test_json_upload_create_with_foreign_submitters_in_list(self) -> None:
        self.assert_with_submitters_in_first_meeting(
            ["noMeeting", "firstMeeting", "secondMeeting", "multiMeeting"]
        )

    def test_json_upload_update_with_foreign_submitters_in_list(self) -> None:
        self.assert_with_submitters_in_first_meeting(
            ["noMeeting", "firstMeeting", "secondMeeting", "multiMeeting"],
            is_update=True,
        )

    def test_json_upload_create_with_submitter_and_multiple_rows(self) -> None:
        self.assert_with_submitters_in_first_meeting("firstMeeting", multiple=True)

    def test_json_upload_update_with_submitter_and_multiple_rows(self) -> None:
        self.assert_with_submitters_in_first_meeting(
            "firstMeeting", is_update=True, multiple=True
        )

    def assert_with_supporters_in_first_meeting(
        self,
        username_data: list[str] | str | None = None,
        add_unknown_user: bool = False,
        is_update: bool = False,
        multiple: bool = False,
    ) -> None:
        meeting_id = 42
        (
            response,
            model_data,
        ) = self.get_user_request_response_and_model_data_in_first_meeting(
            meeting_id,
            {"supporters": username_data},
            add_unknown_user,
            is_update,
            multiple,
        )
        unknown_user_present = add_unknown_user or not username_data
        usernames = (
            [username_data]
            if isinstance(username_data, str)
            else cast(list[str], username_data) or []
        )
        (
            own_meeting_usernames,
            own_meeting_groupless_usernames,
            usernames_to_user_ids,
        ) = self.get_own_meeting_users_groupless_users_and_user_id_dict(
            usernames, meeting_id, model_data
        )
        user_data: UsernameTestAssertionData = {
            "usernames": usernames,
            "own_meeting_usernames": own_meeting_usernames,
            "unknown_user_present": unknown_user_present,
            "usernames_to_user_ids": usernames_to_user_ids,
            "own_meeting_groupless_usernames": own_meeting_groupless_usernames,
        }
        self.make_simple_user_assertions_in_first_meeting(
            response,
            {"supporter": user_data},
            is_update,
            multiple,
        )

    def test_json_upload_create_with_unknown_supporter(self) -> None:
        self.assert_with_supporters_in_first_meeting()

    def test_json_upload_update_with_unknown_supporter(self) -> None:
        self.assert_with_supporters_in_first_meeting(is_update=True)

    def test_json_upload_create_with_simple_supporter(self) -> None:
        self.assert_with_supporters_in_first_meeting("firstMeeting")

    def test_json_upload_update_with_simple_supporter(self) -> None:
        self.assert_with_supporters_in_first_meeting("firstMeeting", is_update=True)

    def test_json_upload_create_with_groupless_supporter(self) -> None:
        self.assert_with_supporters_in_first_meeting("firstMeetingGrouplessSubmitter")

    def test_json_upload_update_with_groupless_supporter(self) -> None:
        self.assert_with_supporters_in_first_meeting(
            "firstMeetingGrouplessSubmitter", is_update=True
        )

    def test_json_upload_create_with_simple_supporter_in_list(self) -> None:
        self.assert_with_supporters_in_first_meeting(["firstMeeting"])

    def test_json_upload_update_with_simple_supporter_in_list(self) -> None:
        self.assert_with_supporters_in_first_meeting(["firstMeeting"], is_update=True)

    def test_json_upload_create_with_two_supporters_in_list(self) -> None:
        self.assert_with_supporters_in_first_meeting(
            ["firstMeeting", "firstMeetingBoth"]
        )

    def test_json_upload_update_with_two_supporters_in_list(self) -> None:
        self.assert_with_supporters_in_first_meeting(
            ["firstMeeting", "firstMeetingBoth"], is_update=True
        )

    def test_json_upload_create_with_unknown_supporter_in_list(self) -> None:
        self.assert_with_supporters_in_first_meeting(
            ["firstMeeting"], add_unknown_user=True
        )

    def test_json_upload_update_with_unknown_supporter_in_list(self) -> None:
        self.assert_with_supporters_in_first_meeting(
            ["firstMeeting"], add_unknown_user=True, is_update=True
        )

    def test_json_upload_create_with_foreign_supporters_in_list(self) -> None:
        self.assert_with_supporters_in_first_meeting(
            ["noMeeting", "firstMeeting", "secondMeeting", "multiMeeting"]
        )

    def test_json_upload_update_with_foreign_supporters_in_list(self) -> None:
        self.assert_with_supporters_in_first_meeting(
            ["noMeeting", "firstMeeting", "secondMeeting", "multiMeeting"],
            is_update=True,
        )

    def test_json_upload_create_with_supporter_and_multiple_rows(self) -> None:
        self.assert_with_supporters_in_first_meeting("firstMeeting", multiple=True)

    def test_json_upload_update_with_supporter_and_multiple_rows(self) -> None:
        self.assert_with_supporters_in_first_meeting(
            "firstMeeting", is_update=True, multiple=True
        )

    def assert_with_both_usertypes_in_first_meeting(
        self,
        submitter_username_data: list[str] | str | None = None,
        supporter_username_data: list[str] | str | None = None,
        add_unknown_user: bool = False,
        is_update: bool = False,
        multiple: bool = False,
    ) -> None:
        meeting_id = 42
        (
            response,
            model_data,
        ) = self.get_user_request_response_and_model_data_in_first_meeting(
            meeting_id,
            {
                "submitters": submitter_username_data,
                "supporters": supporter_username_data,
            },
            add_unknown_user,
            is_update,
            multiple,
        )
        data: UsernameTestExpectationInfo = {}
        for key, username_data in {
            "submitter": submitter_username_data,
            "supporter": supporter_username_data,
        }.items():
            unknown_user_present = add_unknown_user or not username_data
            usernames = (
                [username_data]
                if isinstance(username_data, str)
                else cast(list[str], username_data) or []
            )
            (
                own_meeting_usernames,
                own_meeting_groupless_usernames,
                usernames_to_user_ids,
            ) = self.get_own_meeting_users_groupless_users_and_user_id_dict(
                usernames, meeting_id, model_data
            )
            data[key] = {
                "usernames": usernames,
                "own_meeting_usernames": own_meeting_usernames,
                "unknown_user_present": unknown_user_present,
                "usernames_to_user_ids": usernames_to_user_ids,
                "own_meeting_groupless_usernames": own_meeting_groupless_usernames,
            }
        self.make_simple_user_assertions_in_first_meeting(
            response,
            data,
            is_update,
            multiple,
        )

    def test_json_upload_create_with_both_usertypes_unknown_users(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting()

    def test_json_upload_update_with_both_usertypes_unknown_users(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(is_update=True)

    def test_json_upload_create_with_both_usertypes_simple(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(
            "firstMeeting", "firstMeetingBoth"
        )

    def test_json_upload_update_with_both_usertypes_simple(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(
            "firstMeeting", "firstMeetingBoth", is_update=True
        )

    def test_json_upload_create_with_both_usertypes_and_groupless_user(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(
            "firstMeetingGrouplessSubmitter", "firstMeetingGrouplessSubmitter"
        )

    def test_json_upload_update_with_both_usertypes_and_groupless_user(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(
            "firstMeetingGrouplessSubmitter",
            "firstMeetingGrouplessSubmitter",
            is_update=True,
        )

    def test_json_upload_create_with_both_usertypes_in_lists(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(
            ["firstMeeting"], ["firstMeeting"]
        )

    def test_json_upload_update_with_both_usertypes_in_lists(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(
            ["firstMeeting"], ["firstMeetingSubmitter"], is_update=True
        )

    def test_json_upload_create_with_both_usertypes_unknown_in_list(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(
            ["firstMeeting"], ["multiMeeting"], add_unknown_user=True
        )

    def test_json_upload_update_with_both_usertypes_unknown_in_list(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(
            ["firstMeeting"], ["multiMeeting"], add_unknown_user=True, is_update=True
        )

    def test_json_upload_create_with_both_usertypes_foreign_in_list(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(
            ["noMeeting", "firstMeeting"], ["secondMeeting", "multiMeeting"]
        )

    def test_json_upload_update_with_both_usertypes_foreign_in_list(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(
            ["noMeeting", "firstMeeting"],
            ["secondMeeting", "multiMeeting"],
            is_update=True,
        )

    def test_json_upload_create_with_both_usertypes_and_multiple_rows(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(
            "firstMeeting", "firstMeeting", multiple=True
        )

    def test_json_upload_update_with_both_usertypes_and_multiple_rows(self) -> None:
        self.assert_with_both_usertypes_in_first_meeting(
            "firstMeeting", "firstMeeting", is_update=True, multiple=True
        )

    def assert_with_verbose_users_in_first_meeting(
        self,
        usernames: list[str] | None,
        verbose_usernames: list[str],
        username_fields: list[str] = ["submitter"],
        is_update: bool = False,
        multiple: bool = False,
    ) -> None:
        meeting_id = 42
        rows = 2 if multiple else 1
        self.set_up_models(*self.get_base_user_and_meeting_settings())
        payloads = []
        for i in range(rows):
            payload: dict[str, Any] = {
                "title": "test",
                "text": "my",
            }
            for field in username_fields:
                payload[f"{field}s_verbose"] = verbose_usernames
                if usernames:
                    payload[f"{field}s_username"] = usernames
            if is_update:
                payload["number"] = "NUM0" + str(i + 1)
            payloads.append(payload)
        response = self.request(
            "motion.json_upload",
            {
                "data": payloads,
                "meeting_id": meeting_id,
            },
        )
        has_error = (not not usernames) and len(usernames) < len(verbose_usernames)
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == (2 if multiple else 1)
        assert (
            response.json["results"][0][0]["state"] == ImportState.ERROR
        ) == has_error
        for row in response.json["results"][0][0]["rows"]:
            for user in [
                *(
                    row["data"].get("submitters_username", [])
                    if "submitter" in username_fields
                    else []
                ),
                *(
                    row["data"].get("supporters_username", [])
                    if "supporter" in username_fields
                    else []
                ),
            ]:
                assert (user.get("info") == ImportState.ERROR) == has_error
            assert row["state"] == (
                ImportState.ERROR
                if has_error
                else ImportState.DONE if is_update else ImportState.NEW
            )
            for fieldname in username_fields:
                assert (
                    f"Error: Verbose field is set and has more entries than the username field for {fieldname}s"
                    in row["messages"]
                ) == has_error

    knights = [
        "Sir Galahad the Pure",
        "Sir Bedivere the Wise",
        "Sir Lancelot the Brave",
        "Sir Robin the-not-quite-so-brave-as-Sir-Lancelot",
        "Arthur, King of the Britons",
    ]
    legal_first_meeting_usernames = [
        "firstMeeting",
        "firstMeetingSubmitter",
        "firstMeetingSupporter",
        "firstMeetingBoth",
    ]

    def test_json_upload_create_submitters_less_verbose_fields(self) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames, self.knights[:3]
        )

    def test_json_upload_update_submitters_less_verbose_fields(self) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames, self.knights[:3], is_update=True
        )

    def test_json_upload_create_submitters_less_verbose_fields_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames, self.knights[:3], multiple=True
        )

    def test_json_upload_update_submitters_less_verbose_fields_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames,
            self.knights[:3],
            is_update=True,
            multiple=True,
        )

    def test_json_upload_create_submitters_equal_verbose_fields(self) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames, self.knights[:4]
        )

    def test_json_upload_update_submitters_equal_verbose_fields(self) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames, self.knights[:4], is_update=True
        )

    def test_json_upload_create_submitters_equal_verbose_fields_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames, self.knights[:4], multiple=True
        )

    def test_json_upload_update_submitters_equal_verbose_fields_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames,
            self.knights[:4],
            is_update=True,
            multiple=True,
        )

    def test_json_upload_create_submitters_more_verbose_fields(self) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames, self.knights
        )

    def test_json_upload_update_submitters_more_verbose_fields(self) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames, self.knights, is_update=True
        )

    def test_json_upload_create_submitters_more_verbose_fields_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames, self.knights, multiple=True
        )

    def test_json_upload_update_submitters_more_verbose_fields_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames,
            self.knights,
            is_update=True,
            multiple=True,
        )

    def test_json_upload_create_submitters_with_verbose_fields_no_usernames(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(None, self.knights)

    def test_json_upload_update_submitters_with_verbose_fields_no_usernames(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            None, self.knights, is_update=True
        )

    def test_json_upload_create_submitters_with_verbose_fields_no_usernames_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            None, self.knights, multiple=True
        )

    def test_json_upload_update_submitters_with_verbose_fields_no_usernames_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            None, self.knights, is_update=True, multiple=True
        )

    def test_json_upload_create_supporters_less_verbose_fields(self) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames, self.knights[:3], ["supporter"]
        )

    def test_json_upload_update_supporters_less_verbose_fields(self) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames,
            self.knights[:3],
            ["supporter"],
            is_update=True,
        )

    def test_json_upload_create_supporters_less_verbose_fields_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames,
            self.knights[:3],
            ["supporter"],
            multiple=True,
        )

    def test_json_upload_update_supporters_less_verbose_fields_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames,
            self.knights[:3],
            ["supporter"],
            is_update=True,
            multiple=True,
        )

    def test_json_upload_create_supporters_equal_verbose_fields(self) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames, self.knights[:4], ["supporter"]
        )

    def test_json_upload_update_supporters_equal_verbose_fields(self) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames,
            self.knights[:4],
            ["supporter"],
            is_update=True,
        )

    def test_json_upload_create_supporters_equal_verbose_fields_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames,
            self.knights[:4],
            ["supporter"],
            multiple=True,
        )

    def test_json_upload_update_supporters_equal_verbose_fields_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames,
            self.knights[:4],
            ["supporter"],
            is_update=True,
            multiple=True,
        )

    def test_json_upload_create_supporters_more_verbose_fields(self) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames, self.knights, ["supporter"]
        )

    def test_json_upload_update_supporters_more_verbose_fields(self) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames,
            self.knights,
            ["supporter"],
            is_update=True,
        )

    def test_json_upload_create_supporters_more_verbose_fields_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames,
            self.knights,
            ["supporter"],
            multiple=True,
        )

    def test_json_upload_update_supporters_more_verbose_fields_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            self.legal_first_meeting_usernames,
            self.knights,
            ["supporter"],
            is_update=True,
            multiple=True,
        )

    def test_json_upload_create_supporters_with_verbose_fields_no_usernames(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            None, self.knights, ["supporter"]
        )

    def test_json_upload_update_supporters_with_verbose_fields_no_usernames(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            None, self.knights, ["supporter"], is_update=True
        )

    def test_json_upload_create_supporters_with_verbose_fields_no_usernames_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            None, self.knights, ["supporter"], multiple=True
        )

    def test_json_upload_update_supporters_with_verbose_fields_no_usernames_multiple_rows(
        self,
    ) -> None:
        self.assert_with_verbose_users_in_first_meeting(
            None, self.knights, ["supporter"], is_update=True, multiple=True
        )

    def assert_and_check_for_duplicate_users_in_row(
        self,
        usernames: list[str],
        username_fields: list[str] = ["submitter"],
        is_update: bool = False,
        duplicated_users: list[str] = ["firstMeeting"],
    ) -> None:
        meeting_id = 42
        self.set_up_models(*self.get_base_user_and_meeting_settings())
        payload: dict[str, Any] = {
            "title": "test",
            "text": "my",
        }
        for field in username_fields:
            payload[f"{field}s_username"] = usernames
        if is_update:
            payload["number"] = "NUM01"
        response = self.request(
            "motion.json_upload",
            {
                "data": [payload],
                "meeting_id": meeting_id,
            },
        )
        has_warnings = len(usernames) != len(set(usernames))
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == 1
        assert (
            response.json["results"][0][0]["state"] == ImportState.WARNING
        ) == has_warnings
        row = response.json["results"][0][0]["rows"][0]
        user_set: set[str] = set()
        for user in [
            *row["data"].get("submitters_username", []),
            *row["data"].get("supporters_username", []),
        ]:
            assert (user.get("info") == ImportState.WARNING) == (
                user["value"] in user_set
            )
            user_set.add(user["value"])
        assert row["state"] == (ImportState.DONE if is_update else ImportState.NEW)
        for fieldname in username_fields:
            assert (
                (
                    f"At least one {fieldname} has been referenced multiple times: "
                    in row["messages"][0]
                )
                and all(
                    [
                        duplicated_user in row["messages"][0]
                        for duplicated_user in duplicated_users
                    ]
                )
            ) == has_warnings

    def test_json_upload_create_with_duplicate_submitters(self) -> None:
        self.assert_and_check_for_duplicate_users_in_row(
            [*self.legal_first_meeting_usernames, "firstMeeting", "multiMeeting"]
        )

    def test_json_upload_update_with_duplicate_submitters(self) -> None:
        self.assert_and_check_for_duplicate_users_in_row(
            [
                *self.legal_first_meeting_usernames,
                "firstMeeting",
                "firstMeetingSubmitter",
                "multiMeeting",
            ],
            is_update=True,
            duplicated_users=["firstMeeting", "firstMeetingSubmitter"],
        )

    def test_json_upload_create_with_duplicate_supporters(self) -> None:
        self.assert_and_check_for_duplicate_users_in_row(
            [*self.legal_first_meeting_usernames, "firstMeeting", "multiMeeting"],
            ["supporter"],
        )

    def test_json_upload_update_with_duplicate_supporters(self) -> None:
        self.assert_and_check_for_duplicate_users_in_row(
            [*self.legal_first_meeting_usernames, "firstMeeting", "multiMeeting"],
            ["supporter"],
            is_update=True,
        )

    # -------------------------------------------------------
    # ------------------[ Test with tags ]-------------------
    # -------------------------------------------------------

    def setup_assert_with_tags(
        self,
        base_meeting_id: int = 42,
    ) -> None:
        base_motion_id = 100
        base_tag_id = 1000
        self.set_up_models(
            {
                base_meeting_id: self.get_base_meeting_setting_with_tags(
                    base_motion_id, base_tag_id, ["Got tag go"]
                ),
                (base_meeting_id + 1): self.get_base_meeting_setting_with_tags(
                    base_motion_id * 2, base_tag_id * 2, ["rag-tag"]
                ),
            }
        )

    def assert_with_tags(
        self,
        common_tags: int = 1,
        add_exclusive_tag: bool = False,
        add_unidentifiable_tag: bool = False,
        add_foreign_tag: bool = False,
        add_unknown_tag: bool = False,
        duplicates_in_row: bool = False,
        is_update: bool = False,
        multiple: bool = False,
    ) -> None:
        meeting_id = 42
        self.setup_assert_with_tags(meeting_id)
        use_tags: list[str] = []
        number_of_common_tags = 0
        expected_not_found: list[str] = []
        expect_duplicates = False
        messages: list[str] = []
        if common_tags:
            number_of_common_tags = max(min(common_tags, 3), 1)
            use_tags = ["Tag-liatelle", "Tag-you're-it", "Price tag"][
                :number_of_common_tags
            ]
        if add_exclusive_tag:
            use_tags.append("Got tag go")
        if add_unidentifiable_tag:
            use_tags.append("Tag-ether")
            messages.append("Found multiple tags with the same name: Tag-ether")
        if add_foreign_tag:
            use_tags.append("rag-tag")
            expected_not_found.append("rag-tag")
        if add_unknown_tag:
            use_tags.append("Not a tag")
            expected_not_found.append("Not a tag")
        if duplicates_in_row:
            if number_of_common_tags:
                use_tags.append("Tag-liatelle")
            else:
                number_of_common_tags = 1
                use_tags = ["Tag-liatelle", *use_tags, "Tag-liatelle"]
            expect_duplicates = True
            messages.append(
                "At least one tag has been referenced multiple times: Tag-liatelle"
            )
        has_warnings = (
            add_unidentifiable_tag or len(expected_not_found) or expect_duplicates
        )
        expected_data: list[dict[str, Any]] = []
        for i in range(len(use_tags)):
            tag = use_tags[i]
            if number_of_common_tags > 0:
                expected_data.append(
                    {"info": ImportState.DONE, "id": 1000 + i, "value": tag}
                )
                number_of_common_tags -= 1
            elif add_exclusive_tag:
                expected_data.append(
                    {"info": ImportState.DONE, "id": 1000 + 5, "value": tag}
                )
                add_exclusive_tag = False
            else:
                expected_data.append({"info": ImportState.WARNING, "value": tag})
        rows = 2 if multiple else 1
        payloads: list[dict[str, Any]] = []
        for i in range(rows):
            payload: dict[str, Any] = {
                "title": "Tagged",
                "text": "to infinity",
                "tags": use_tags,
            }
            if is_update:
                payload["number"] = f"NUM0{i + 1}"
            payloads.append(payload)
        response = self.request(
            "motion.json_upload",
            {
                "data": payloads,
                "meeting_id": meeting_id,
            },
        )
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == rows
        assert response.json["results"][0][0]["state"] == (
            ImportState.WARNING if has_warnings else ImportState.DONE
        )
        for i in range(rows):
            row = response.json["results"][0][0]["rows"][i]
            assert row["state"] == (ImportState.DONE if is_update else ImportState.NEW)
            row_data = row.get("data", {})
            assert row_data.get("tags") == expected_data
            assert (
                len(row.get("messages", [])) == len(messages)
                if not len(expected_not_found)
                else len(messages) + 1
            )
            for message in messages:
                assert message in row["messages"]
            if len(expected_not_found):
                assert (
                    len(
                        [
                            message
                            for message in row["messages"]
                            if message.startswith("Could not find at least one tag: ")
                            and all([name in message for name in expected_not_found])
                        ]
                    )
                    == 1
                )

    def test_json_upload_create_with_tags(self) -> None:
        self.assert_with_tags(3)

    def test_json_upload_update_with_tags(self) -> None:
        self.assert_with_tags(3, add_exclusive_tag=True, is_update=True)

    def test_json_upload_create_multiple_motions_with_tags(self) -> None:
        self.assert_with_tags(
            3, add_exclusive_tag=True, add_unidentifiable_tag=True, multiple=True
        )

    def test_json_upload_update_multiple_motions_with_tags(self) -> None:
        self.assert_with_tags(
            3,
            add_exclusive_tag=True,
            add_unidentifiable_tag=True,
            add_foreign_tag=True,
            is_update=True,
            multiple=True,
        )

    def test_json_upload_create_with_tags_2(self) -> None:
        self.assert_with_tags(
            3,
            add_exclusive_tag=True,
            add_unidentifiable_tag=True,
            add_foreign_tag=True,
            add_unknown_tag=True,
        )

    def test_json_upload_update_with_tags_2(self) -> None:
        self.assert_with_tags(
            1,
            add_exclusive_tag=True,
            add_unidentifiable_tag=True,
            add_foreign_tag=True,
            add_unknown_tag=True,
            duplicates_in_row=True,
            is_update=True,
        )

    def test_json_upload_create_multiple_motions_with_tags_2(self) -> None:
        self.assert_with_tags(
            1,
            add_unidentifiable_tag=True,
            add_foreign_tag=True,
            add_unknown_tag=True,
            duplicates_in_row=True,
            multiple=True,
        )

    def test_json_upload_update_multiple_motions_with_tags_2(self) -> None:
        self.assert_with_tags(
            1,
            add_foreign_tag=True,
            add_unknown_tag=True,
            duplicates_in_row=True,
            is_update=True,
            multiple=True,
        )

    def test_json_upload_create_with_tags_3(self) -> None:
        self.assert_with_tags(1, add_unknown_tag=True, duplicates_in_row=True)

    def test_json_upload_update_with_tags_3(self) -> None:
        self.assert_with_tags(1, duplicates_in_row=True, is_update=True)

    def test_json_upload_create_multiple_motions_with_tags_3(self) -> None:
        self.assert_with_tags(0, multiple=True)

    def test_json_upload_update_multiple_motions_with_tags_3(self) -> None:
        self.assert_with_tags(
            0, add_unidentifiable_tag=True, is_update=True, multiple=True
        )

    def test_json_upload_create_with_tags_4(self) -> None:
        self.assert_with_tags(0, add_foreign_tag=True, duplicates_in_row=True)

    def test_json_upload_update_with_tags_4(self) -> None:
        self.assert_with_tags(0, add_unknown_tag=True, is_update=True)

    def test_json_upload_create_multiple_motions_with_tags_4(self) -> None:
        self.assert_with_tags(
            0, add_exclusive_tag=True, duplicates_in_row=True, multiple=True
        )

    def test_json_upload_update_multiple_motions_with_tags_4(self) -> None:
        self.assert_with_tags(
            3,
            add_unidentifiable_tag=True,
            add_unknown_tag=True,
            is_update=True,
            multiple=True,
        )

    # -------------------------------------------------------
    # ------------------[ Test with block ]------------------
    # -------------------------------------------------------

    def setup_assert_with_blocks(
        self,
        base_meeting_id: int = 42,
    ) -> None:
        base_motion_id = 100
        base_block_id = 1000
        self.set_up_models(
            {
                base_meeting_id: self.get_base_meeting_setting_with_blocks(
                    base_motion_id, base_block_id, ["Block and roll"]
                ),
                (base_meeting_id + 1): self.get_base_meeting_setting_with_blocks(
                    base_motion_id * 2, base_block_id * 2, ["Blocked"]
                ),
            }
        )

    def assert_with_blocks(
        self,
        block: str,
        expected_id: int | None = None,
        expected_message: str | None = None,
        is_update: bool = False,
        multiple: bool = False,
    ) -> None:
        meeting_id = 42
        self.setup_assert_with_blocks(meeting_id)
        messages: list[str] = []
        rows = 2 if multiple else 1
        payloads: list[dict[str, Any]] = []
        for i in range(rows):
            payload: dict[str, Any] = {
                "title": "Blocks",
                "text": "are cool",
                "block": block,
            }
            if is_update:
                payload["number"] = f"NUM0{i + 1}"
            payloads.append(payload)
        response = self.request(
            "motion.json_upload",
            {
                "data": payloads,
                "meeting_id": meeting_id,
            },
        )
        expected_data: dict[str, Any] = {
            "info": ImportState.WARNING if expected_message else ImportState.DONE,
            "value": block,
        }
        if expected_id:
            expected_data["id"] = expected_id
        self.assert_status_code(response, 200)
        assert len(response.json["results"][0][0]["rows"]) == rows
        assert response.json["results"][0][0]["state"] == (
            ImportState.WARNING if expected_message else ImportState.DONE
        )
        for i in range(rows):
            row = response.json["results"][0][0]["rows"][i]
            assert row["state"] == (ImportState.DONE if is_update else ImportState.NEW)
            row_data = row.get("data", {})
            assert row_data.get("block") == expected_data
            assert len(row.get("messages", [])) == (1 if expected_message else 0)
            for message in messages:
                assert message in row["messages"]

    def test_json_upload_create_with_simple_block(self) -> None:
        self.assert_with_blocks("Block and roll", 1005)

    def test_json_upload_update_with_simple_block(self) -> None:
        self.assert_with_blocks("Block and roll", 1005, is_update=True)

    def test_json_upload_create_multiple_motions_with_simple_block(self) -> None:
        self.assert_with_blocks("Block and roll", 1005, multiple=True)

    def test_json_upload_update_multiple_motions_with_simple_block(self) -> None:
        self.assert_with_blocks("Block and roll", 1005, is_update=True, multiple=True)

    def test_json_upload_create_with_multi_meeting_block(self) -> None:
        self.assert_with_blocks("Blockolade", 1000)

    def test_json_upload_update_with_multi_meeting_block(self) -> None:
        self.assert_with_blocks("Blockodile", 1001, is_update=True)

    def test_json_upload_create_multiple_motions_with_multi_meeting_block(self) -> None:
        self.assert_with_blocks("Blockoli", 1002, multiple=True)

    def test_json_upload_update_multiple_motions_with_multi_meeting_block(self) -> None:
        self.assert_with_blocks("Blockolade", 1000, is_update=True, multiple=True)

    def test_json_upload_create_with_unidentifiable_block(self) -> None:
        self.assert_with_blocks(
            "Block chain",
            expected_message="Found multiple motion blocks with the same name",
        )

    def test_json_upload_update_with_unidentifiable_block(self) -> None:
        self.assert_with_blocks(
            "Block chain",
            expected_message="Found multiple motion blocks with the same name",
            is_update=True,
        )

    def test_json_upload_create_multiple_motions_with_unidentifiable_block(
        self,
    ) -> None:
        self.assert_with_blocks(
            "Block chain",
            expected_message="Found multiple motion blocks with the same name",
            multiple=True,
        )

    def test_json_upload_update_multiple_motions_with_unidentifiable_block(
        self,
    ) -> None:
        self.assert_with_blocks(
            "Block chain",
            expected_message="Found multiple motion blocks with the same name",
            is_update=True,
            multiple=True,
        )

    def test_json_upload_create_with_foreign_block(self) -> None:
        self.assert_with_blocks(
            "Blocked", expected_message="Could not find motion block"
        )

    def test_json_upload_update_with_foreign_block(self) -> None:
        self.assert_with_blocks(
            "Blocked", expected_message="Could not find motion block", is_update=True
        )

    def test_json_upload_create_multiple_motions_with_foreign_block(self) -> None:
        self.assert_with_blocks(
            "Blocked", expected_message="Could not find motion block", multiple=True
        )

    def test_json_upload_update_multiple_motions_with_foreign_block(self) -> None:
        self.assert_with_blocks(
            "Blocked",
            expected_message="Could not find motion block",
            is_update=True,
            multiple=True,
        )

    def test_json_upload_create_with_unknown_block(self) -> None:
        self.assert_with_blocks(
            "James Block", expected_message="Could not find motion block"
        )

    def test_json_upload_update_with_unknown_block(self) -> None:
        self.assert_with_blocks(
            "James Block",
            expected_message="Could not find motion block",
            is_update=True,
        )

    def test_json_upload_create_multiple_motions_with_unknown_block(self) -> None:
        self.assert_with_blocks(
            "James Block", expected_message="Could not find motion block", multiple=True
        )

    def test_json_upload_update_multiple_motions_with_unknown_block(self) -> None:
        self.assert_with_blocks(
            "James Block",
            expected_message="Could not find motion block",
            is_update=True,
            multiple=True,
        )
