from typing import Any, Dict

from ....models.models import User
from ....services.datastore.commands import GetManyRequest
from ....shared.exceptions import ActionException
from ....shared.patterns import ID_REGEX, Collection
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user.update")
class UserUpdate(UpdateAction):
    """
    Action to update a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_update_schema(
        optional_properties=[
            "username",
            "title",
            "first_name",
            "last_name",
            "is_active",
            "is_physical_person",
            "gender",
            "email",
            "default_number",
            "default_structure_level",
            "default_vote_weight",
            "organisation_management_level",
            "is_present_in_meeting_ids",
            "guest_meeting_ids",
            "committee_as_member_ids",
            "committee_as_manager_ids",
        ],
        additional_optional_fields={
            "group_ids": id_list_schema,
            "vote_delegations_from_ids": {
                "type": "object",
                "patternProperties": {ID_REGEX: id_list_schema},
                "additionalProperties": False,
            },
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if instance.get("group_ids"):
            group_ids = instance.pop("group_ids")
            gmr = GetManyRequest(
                Collection("group"),
                group_ids,
                ["meeting_id"],
            )
            result = self.datastore.get_many([gmr])
            db_groups = result.get(Collection("group"), {})
            if len(db_groups) != len(group_ids):
                raise ActionException("Invalid group ids given")
            for id, group in db_groups.items():
                field = f"group_${group['meeting_id']}_ids"
                if field not in instance:
                    instance[field] = [id]
                else:
                    instance[field] += [id]
        if instance.get("vote_delegations_from_ids"):
            # TODO: check if delegation is valid (see OS3 code)
            vote_delegations = instance.pop("vote_delegations_from_ids")
            for meeting_id, user_ids in vote_delegations.items():
                instance[f"vote_delegations_${meeting_id}_from_ids"] = user_ids
        return instance
