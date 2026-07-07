from typing import Any

from openslides_backend.shared.exceptions import ActionException

from ....models.models import MeetingPollDefault, Poll
from ....shared.filters import FilterOperator
from ...generics.create import CreateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("meeting_poll_default.create", action_type=ActionType.BACKEND_INTERNAL)
class MeetingPollDefaultCreate(CreateAction):
    """
    Action to create a meeting_poll_default.
    """

    model = MeetingPollDefault()
    schema = DefaultSchema(MeetingPollDefault()).get_create_schema(
        required_properties=["meeting_id"],
        optional_properties=[
            "used_as_assignment_poll_config_in_meeting_id",
            "used_as_motion_poll_config_in_meeting_id",
            "used_as_topic_poll_config_in_meeting_id",
            "allow_abstain",
            "allow_nota",
            "display_chart",
            "group_ids",
            "onehundred_percent_base",
            "sort_result_by_votes",
            "strike_out",
            "visibility",
        ],
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        poll_types_fields = {
            field_name: value
            for field_name in MeetingPollDefault.POLL_TYPE_FIELDS
            if (value := instance.get(field_name))
        }
        self.check_exactly_one_of(instance, poll_types_fields)

        # Checks below are reachable only if exactly one poll type field is set
        poll_type_field_name, poll_type_field_value = next(
            iter(poll_types_fields.items())
        )
        self.check_equal_fields(instance, poll_type_field_name, poll_type_field_value)
        self.check_prevent_updates(instance, poll_type_field_name)

        if "visibility" not in instance:
            instance["visibility"] = (
                Poll.VISIBILITY_MANUALLY
                if poll_type_field_name == "used_as_topic_poll_config_in_meeting_id"
                else Poll.VISIBILITY_SECRET
            )

        if (
            poll_type_field_name == "used_as_topic_poll_config_in_meeting_id"
            and "display_chart" not in instance
        ):
            instance["display_chart"] = "pie"

        return super().update_instance(instance)

    def check_exactly_one_of(
        self, instance: dict[str, Any], poll_types_fields: dict[str, int]
    ) -> None:
        """
        Checks that exactly one of the poll type fields is defined for the instance:
            - used_as_assignment_poll_config_in_meeting_id
            - used_as_motion_poll_config_in_meeting_id
            - used_as_topic_poll_config_in_meeting_id
        """
        # TODO: replace with exactly_one_of constraint (https://github.com/OpenSlides/openslides-meta/issues/540)
        if not len(poll_types_fields):
            raise ActionException(
                f"One of the fields {MeetingPollDefault.POLL_TYPE_FIELDS} must be set."
            )
        if len(poll_types_fields) > 1:
            raise ActionException(
                f"Only one of {MeetingPollDefault.POLL_TYPE_FIELDS} can be set."
            )

    def check_equal_fields(
        self,
        instance: dict[str, Any],
        poll_type_field_name: str,
        poll_type_field_value: int,
    ) -> None:
        """
        Checks that value in poll type field matches the meeting_id.
        """
        # TODO: replace with the updated equal_fields constraint (https://github.com/OpenSlides/openslides-meta/issues/541)
        if poll_type_field_value != instance["meeting_id"]:
            raise ActionException(
                f"Values in fields '{poll_type_field_name}' and 'meeting_id' don't match."
            )

    def check_prevent_updates(
        self, instance: dict[str, Any], poll_type_field_name: str
    ) -> None:
        """
        Prevents creating a new meeting_poll_default item if meeting already
        contains meeting_poll_default for the same poll type.
        """
        # TODO: replace with the updated prevent_updates constraint (https://github.com/OpenSlides/openslides-meta/issues/542)
        meeting_id = instance["meeting_id"]
        if self.datastore.filter(
            "meeting_poll_default",
            FilterOperator(poll_type_field_name, "=", meeting_id),
            ["id"],
            lock_result=False,
        ):
            raise ActionException(
                f"'{poll_type_field_name}' already exists in meeting/{meeting_id}."
            )
