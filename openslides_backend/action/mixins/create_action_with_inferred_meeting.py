from typing import Any, Dict, Type, cast

from ...models.fields import BaseGenericRelationField, BaseRelationField
from ...shared.exceptions import ActionException
from ...shared.patterns import FullQualifiedId, to_fqid
from ..generics.create import CreateAction


class CreateActionWithInferredMeetingMixin(CreateAction):
    """
    Mixin to automatically set the meeting_id on create if it's not given in the action data.
    The given relation_field_for_meeting must be a relation field.
    """

    relation_field_for_meeting: str

    def update_instance_with_meeting_id(
        self, instance: Dict[str, Any]
    ) -> Dict[str, Any]:
        instance["meeting_id"] = self.get_meeting_id(instance)
        return instance

    def get_meeting_id(self, instance: Dict[str, Any]) -> int:
        field = self.model.get_field(self.relation_field_for_meeting)
        assert isinstance(field, BaseRelationField)
        id = instance[self.relation_field_for_meeting]
        if isinstance(field, BaseGenericRelationField):
            fqid = cast(FullQualifiedId, id)
        else:
            assert len(field.to) == 1
            fqid = to_fqid(field.get_target_collection(), id)
        # Fetch meeting_id
        related_model = self.datastore.get(
            fqid,
            ["meeting_id"],
        )
        if not related_model.get("meeting_id"):
            raise ActionException(
                f"Referenced model in field {self.relation_field_for_meeting} has no meeting id."
            )
        return related_model["meeting_id"]


class CreateActionWithInferredMeeting(
    CreateActionWithInferredMeetingMixin, CreateAction
):
    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        return self.update_instance_with_meeting_id(instance)


def get_create_action_with_inferred_meeting(
    relation_field_for_meeting: str,
) -> Type[CreateActionWithInferredMeeting]:
    """
    Shortcut to get a CreateAction class with inferred meeting.

        MyAction = get_create_action_with_inferred_meeting("foo")

    is equal to

        class MyAction(CreateActionWithInferredMeeting):
            relation_field_for_meeting = "foo"
    """
    return type(
        CreateActionWithInferredMeeting.__name__ + "_" + relation_field_for_meeting,
        (CreateActionWithInferredMeeting,),
        dict(relation_field_for_meeting=relation_field_for_meeting),
    )
