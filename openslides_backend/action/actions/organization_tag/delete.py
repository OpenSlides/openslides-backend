from ....action.util.typing import ActionData, ActionResults
from ....models.models import OrganizationTag
from ....permissions.management_levels import OrganizationManagementLevel
from ...ddaction import DDAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("organization_tag.delete")
class OrganizationTagDelete(DDAction):
    """
    Action to delete a organization tag.
    """

    model = OrganizationTag()
    schema = DefaultSchema(OrganizationTag()).get_delete_schema()
    permission = OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    skip_archived_meeting_check = True

    def write_instances(self, action_data: ActionData) -> ActionResults | None:
        instances = list(action_data)
        self.database.delete_models(
            "gm_organization_tag_tagged_ids_t",
            [{"organization_tag_id": instance["id"]} for instance in instances],
            [],
            match_on=["organization_tag_id"],
        )
        self.database.delete_models(self.model.collection, instances, [])
        return None
