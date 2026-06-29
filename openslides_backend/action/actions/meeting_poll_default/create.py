from typing import Any

from openslides_backend.shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ....models.models import MeetingPollDefault
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...generics.create import CreateAction


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
            "ballot_paper_selection",
            "ballot_paper_number",
            "sort_result_by_votes",
            "visibility",
            "allow_abstain",
            "allow_nota",
            "strike_out",
            "onehundred_percent_base",
            "group_ids",
            "display_chart",
        ],
    )

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        poll_types_fields = {
            field_name: value
            for field_name in MeetingPollDefault.POLL_TYPE_FIELDS
            if (value := instance.get(field_name))
        }
        self.check_exactly_one_of(instance, poll_types_fields)
        self.check_equal_fields(instance, poll_types_fields)
        self.check_prevent_updates(instance, poll_types_fields)
        return super().update_instance(instance)

    def check_exactly_one_of(self, instance, poll_types_fields):
        # TODO: replace with exactly_one_of constraint (https://github.com/OpenSlides/openslides-meta/issues/540)
        if not len(poll_types_fields):
            raise ActionException(
                f"One of the fields {MeetingPollDefault.POLL_TYPE_FIELDS} must be set."
            )
        if len(poll_types_fields) > 1:
            raise ActionException(
                f"Only one of {MeetingPollDefault.POLL_TYPE_FIELDS} can be set."
            )

    def check_equal_fields(self, instance, poll_types_fields):
        # TODO: replace with the updated equal_fields constraint (https://github.com/OpenSlides/openslides-meta/issues/541)
        poll_type_field_name, poll_type_field_value = next(
            iter(poll_types_fields.items())
        )
        if poll_type_field_value != instance["meeting_id"]:
            raise ActionException(
                f"Values in fields '{poll_type_field_name}' and 'meeting_id' don't match."
            )

    def check_prevent_updates(self, instance, poll_types_fields):
        # TODO: replace with the updated prevent_updates constraint (https://github.com/OpenSlides/openslides-meta/issues/542)
        poll_type_field_name, poll_type_field_value = next(
            iter(poll_types_fields.items())
        )
        meeting_id = instance["meeting_id"]
        exists = self.datastore.filter(
            "meeting_poll_default",
            FilterOperator(poll_type_field_name, "=", meeting_id),
            ["id"],
            lock_result=False,
        )
        if exists:
            # if self.get_meeting_poll_default(meeting_id, poll_type_field_name):
            raise ActionException(
                f"'{poll_type_field_name}' already exists in meeting/{meeting_id}."
            )
