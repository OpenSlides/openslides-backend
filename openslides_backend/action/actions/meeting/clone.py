from datetime import datetime
from decimal import Decimal
from typing import Any, cast

from openslides_backend.action.actions.meeting.mixins import MeetingPermissionMixin
from openslides_backend.models.checker import (
    Checker,
    CheckException,
    external_motion_fields,
)
from openslides_backend.models.models import Meeting, MeetingUser
from openslides_backend.services.database.interface import GetManyRequest
from openslides_backend.shared.exceptions import ActionException, PermissionDenied
from openslides_backend.shared.interfaces.event import Event, EventType
from openslides_backend.shared.patterns import fqid_from_collection_and_id
from openslides_backend.shared.schema import id_list_schema, required_id_schema
from openslides_backend.shared.util import ONE_ORGANIZATION_ID

from ....shared.export_helper import export_meeting
from ...mixins.forward_mediafiles_mixin import ForwardMediafilesMixin
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .import_ import MeetingImport

updatable_fields = [
    "committee_id",
    "welcome_title",
    "description",
    "start_time",
    "end_time",
    "location",
    "organization_tag_ids",
    "name",
    "external_id",
]


@register_action("meeting.clone")
class MeetingClone(ForwardMediafilesMixin, MeetingImport):
    """
    Action to clone a meeting.
    """

    schema = DefaultSchema(Meeting()).get_default_schema(
        optional_properties=updatable_fields,
        additional_required_fields={"meeting_id": required_id_schema},
        additional_optional_fields={
            "user_ids": id_list_schema,
            "admin_ids": id_list_schema,
            "set_as_template": {"type": "boolean"},
        },
    )
    action_name = "clone"

    def prefetch(self, action_data: ActionData) -> None:
        self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting",
                    list({instance["meeting_id"] for instance in action_data}),
                    ["committee_id"],
                ),
                GetManyRequest(
                    "organization",
                    [ONE_ORGANIZATION_ID],
                    [
                        "active_meeting_ids",
                        "archived_meeting_ids",
                        "limit_of_meetings",
                    ],
                ),
            ],
            use_changed_models=False,
        )

    def preprocess_data(self, instance: dict[str, Any]) -> dict[str, Any]:
        # overwrite method from meeting.import
        return instance

    def check_permissions(self, instance: dict[str, Any]) -> None:
        if "committee_id" in instance:
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", instance["meeting_id"]),
                ["committee_id", "template_for_organization_id"],
                lock_result=False,
            )
            if meeting["committee_id"] != instance["committee_id"] and not meeting.get(
                "template_for_organization_id"
            ):
                raise PermissionDenied(
                    "Cannot clone meeting to a different committee if it is a non-template meeting."
                )
        MeetingPermissionMixin.check_permissions(self, instance)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        meeting_json = export_meeting(self.datastore, instance["meeting_id"], True)
        instance["meeting"] = meeting_json
        additional_user_ids = instance.pop("user_ids", None) or []
        additional_admin_ids = instance.pop("admin_ids", None) or []
        set_as_template = instance.pop("set_as_template", False)

        # needs an empty map for superclass code
        self.merge_user_map = {
            int(id_): int(id_) for id_ in meeting_json.get("user", {})
        }
        self.number_of_imported_users = len(self.merge_user_map)
        self.number_of_merged_users = len(self.merge_user_map)

        # checks if the meeting is correct
        self.check_one_meeting(instance)
        meeting = self.get_meeting_from_json(meeting_json)

        if committee_id := instance.get("committee_id"):
            meeting["committee_id"] = committee_id

        # pre update the meeting
        if "name" not in instance:
            suffix = " - Copy"
            max_length = Meeting().name.constraints.get("maxLength")
            old_name = meeting["name"]
            if max_length and len(old_name) + len(suffix) > max_length:
                meeting["name"] = (
                    old_name[: max_length - len(suffix) - 3] + "..." + suffix
                )
            else:
                meeting["name"] = old_name + suffix

        # Set proper types for TimestampFields
        for field_name in ["start_time", "end_time"]:
            if (value := instance.get(field_name)) and isinstance(value, int):
                instance[field_name] = datetime.fromtimestamp(value)

        meeting.pop("external_id", "")
        for field in updatable_fields:
            if field in instance:
                meeting[field] = instance.pop(field)

        vote_weight_min = Decimal(
            MeetingUser.vote_weight.constraints.get("minimum", "0.000001")
        )
        for meeting_user in meeting_json.get("meeting_user", {}).values():
            if (value := meeting_user.get("vote_weight")) is not None:
                if Decimal(value) < vote_weight_min:
                    meeting_user["vote_weight"] = "0.000001"
            else:
                user_id = meeting_user.get("user_id", 0)
                value = (
                    meeting_json.get("user", {})
                    .get(str(user_id), "0")
                    .get("default_vote_weight")
                )
                if value is not None and Decimal(value) < vote_weight_min:
                    meeting_user["vote_weight"] = "0.000001"

        # Necessary, because the check otherwise raise exception, even if user will not be imported
        for user in meeting_json.get("user", {}).values():
            if (value := user.get("default_vote_weight")) is not None:
                if Decimal(value) < vote_weight_min:
                    user["default_vote_weight"] = "0.000001"

        # Necessary for orga-wide mediafiles
        mediafiles = self.datastore.get_many(
            [
                GetManyRequest(
                    "mediafile",
                    [
                        mm.get("mediafile_id")
                        for mm in meeting_json.get("meeting_mediafile", {}).values()
                    ],
                    [
                        "id",
                        "mimetype",
                        "owner_id",
                        "meeting_mediafile_ids",
                        "published_to_meetings_in_organization_id",
                    ],
                ),
            ],
            use_changed_models=False,
        )["mediafile"]
        meeting_json["mediafile"] = {
            str(id_): data
            for id_, data in mediafiles.items()
            if data.pop("meta_position", True) or True
        }

        # check datavalidation
        checker = Checker(
            data=meeting_json,
            mode="internal",
            repair=True,
            fields_to_remove={
                "motion": external_motion_fields,
            },
        )
        try:
            checker.run_check()
        except CheckException as ce:
            raise ActionException(str(ce))
        self.allowed_collections = checker.allowed_collections

        # set active
        meeting["is_active_in_organization_id"] = ONE_ORGANIZATION_ID
        meeting.pop("is_archived_in_organization_id", 0)
        meeting["template_for_organization_id"] = (
            ONE_ORGANIZATION_ID if set_as_template else None
        )

        # check limit of meetings
        self.check_limit_of_meetings(
            text="clone",
            text2="",
        )
        # set imported_at
        meeting["imported_at"] = datetime.now()

        mediafiles = {
            int(id_): data for id_, data in meeting_json.pop("mediafile", {}).items()
        }
        origin_meeting_mediafiles = meeting_json.pop("meeting_mediafile", {})

        self.create_replace_map(meeting_json)
        self._remove_mediafile_relational_fields(meeting_json)
        meeting_mediafiles = self._update_meeting_mediafiles(
            origin_meeting_mediafiles, meeting["id"]
        )
        self.replace_fields(instance)

        meeting_id = meeting["id"]
        self.perform_mediafiles_duplication(
            {
                "mediafile": mediafiles,
                "meeting_mediafile": meeting_mediafiles,
            }
        )
        meeting_users_in_instance = instance["meeting"]["meeting_user"]
        if additional_user_ids:
            default_group_id = meeting.get("default_group_id")
            group_in_instance = instance["meeting"]["group"][str(default_group_id)]
            self._update_default_and_admin_group(
                group_in_instance,
                meeting_users_in_instance,
                additional_user_ids,
                meeting_id,
            )

        if additional_admin_ids:
            admin_group_id = meeting.get("admin_group_id")
            group_in_instance = instance["meeting"]["group"][str(admin_group_id)]
            self._update_default_and_admin_group(
                group_in_instance,
                meeting_users_in_instance,
                additional_admin_ids,
                meeting_id,
            )
            if not set_as_template and not len(
                group_in_instance.get("meeting_user_ids", [])
            ):
                raise ActionException(
                    "Cannot create a non-template meeting without administrators"
                )
        elif not set_as_template and any(
            [
                not len(group.get("meeting_user_ids", []))
                for group in meeting_json["group"].values()
                if group.get("admin_group_for_meeting_id")
            ]
        ):
            raise ActionException(
                "Cannot create a non-template meeting without administrators"
            )
        return instance

    def _create_or_get_meeting_user(self, meeting_id: int, user_id: int) -> int:
        meeting_user = self.get_meeting_user(meeting_id, user_id, ["id"])
        if meeting_user:
            return meeting_user["id"]
        else:
            meeting_user_id = self.create_meeting_user(meeting_id, user_id)
            self.datastore.get_changed_model("meeting_user", meeting_user_id).pop(
                "meta_new", None
            )
            return meeting_user_id

    def _update_default_and_admin_group(
        self,
        group_in_instance: dict[str, Any],
        meeting_users_in_instance: dict[str, Any],
        additional_user_ids: list[int],
        meeting_id: int,
    ) -> None:
        additional_meeting_user_ids = [
            self._create_or_get_meeting_user(meeting_id, user_id)
            for user_id in additional_user_ids
        ]
        meeting_user_ids = set(
            group_in_instance.get("meeting_user_ids", set()) or set()
        )
        meeting_user_ids.update(additional_meeting_user_ids)
        group_id = group_in_instance["id"]
        for meeting_user_id in additional_meeting_user_ids:
            meeting_user = cast(
                dict[str, Any],
                self.datastore.get_changed_model("meeting_user", meeting_user_id),
            )
            group_ids = meeting_user.get("group_ids", [])
            if group_id not in group_ids:
                group_ids.append(group_id)
                meeting_user["group_ids"] = group_ids
            meeting_users_in_instance[str(meeting_user_id)] = meeting_user
        group_in_instance["meeting_user_ids"] = list(meeting_user_ids)

    def append_extra_events(
        self, events: list[Event], json_data: dict[str, Any]
    ) -> None:
        meeting_id = self.get_meeting_from_json(json_data)["id"]
        if organization_tag_ids := self.get_meeting_from_json(json_data).get(
            "organization_tag_ids"
        ):
            meeting_fqid = fqid_from_collection_and_id("meeting", meeting_id)
            for organization_tag_id in organization_tag_ids:
                events.append(
                    self.build_event(
                        EventType.Update,
                        fqid_from_collection_and_id(
                            "organization_tag", organization_tag_id
                        ),
                        list_fields={
                            "add": {
                                "tagged_ids": [meeting_fqid],
                            },
                            "remove": {},
                        },
                    ),
                )

    def get_committee_id(self, instance: dict[str, Any]) -> int:
        if instance.get("committee_id"):
            return instance["committee_id"]
        else:
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", instance["meeting_id"]),
                ["committee_id"],
                lock_result=False,
                use_changed_models=False,
            )
            return meeting["committee_id"]

    def _remove_mediafile_relational_fields(
        self, meeting: dict[str, dict[str, Any]]
    ) -> None:
        """
        All the meeting_mediafile relations are handled by ForwardMediafilesMixin
        so shouldn't be processed in this class.
        """
        meeting_fields_to_skip = [
            field.own_field_name
            for field in Meeting().get_fields()
            if field.own_field_name.startswith(("logo_", "font_"))
        ] + ["mediafile_ids", "meeting_mediafile_ids"]
        group_fields_to_skip = [
            "meeting_mediafile_access_group_ids",
            "meeting_mediafile_inherited_access_group_ids",
        ]

        self._strip_instance_fields(meeting["meeting"], meeting_fields_to_skip)
        self._strip_instance_fields(meeting["group"], group_fields_to_skip)

    def _strip_instance_fields(
        self,
        collection: dict[str, Any],
        fields_to_strip: list[str],
    ) -> None:
        """
        Removes from the instance the fields that shouldn't be processed
        (for example, because they are processed in other actions).
        """
        for entry in collection.values():
            for field in fields_to_strip:
                entry.pop(field, None)

    def _update_meeting_mediafiles(
        self, origin_meeting_mediafiles: dict[str, dict[str, Any]], meeting_id: int
    ) -> dict[int, dict[str, Any]]:
        return {
            int(id_): {
                **data,
                "target_meeting_ids": [
                    self.replace_map.get("meeting", {}).get(meeting_id)
                ],
                **{
                    field: [
                        self.replace_map.get("group", {}).get(group_id)
                        for group_id in data.get(field, [])
                    ]
                    for field in ["access_group_ids", "inherited_access_group_ids"]
                    if field in data
                },
            }
            for id_, data in origin_meeting_mediafiles.items()
        }
