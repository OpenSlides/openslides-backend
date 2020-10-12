from typing import Any, Dict, Type

from ..models.fields import BaseGenericRelationField, BaseRelationField
from ..shared.exceptions import ActionException
from ..shared.patterns import FullQualifiedId
from .generics import CreateAction


class CreateActionWithInferredMeetingMixin(CreateAction):
    """
    Mixin to autmatically set the meeting_id on create if it's not given in the payload.
    The given relation_field_for_meeting must be a relation field.
    """

    relation_field_for_meeting: str

    def update_instance_with_meeting_id(
        self, instance: Dict[str, Any]
    ) -> Dict[str, Any]:
        field = self.model.get_field(self.relation_field_for_meeting)
        assert isinstance(field, BaseRelationField)
        id = instance[self.relation_field_for_meeting]
        if isinstance(field, BaseGenericRelationField):
            fqid = id
        else:
            assert not isinstance(field.to, list)  # for mypy
            fqid = FullQualifiedId(field.to, id)
        # Fetch meeting_id
        related_model = self.fetch_model(fqid, ["meeting_id"])
        if not related_model.get("meeting_id"):
            raise ActionException(
                f"Referenced model in field {self.relation_field_for_meeting} has no meeting id."
            )
        instance["meeting_id"] = related_model["meeting_id"]
        return instance


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
