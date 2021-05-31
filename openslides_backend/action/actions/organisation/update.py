from typing import Any, Dict

from ....models.models import Organisation
from ....permissions.management_levels import OrganisationManagementLevel
from ....permissions.permission_helper import has_organisation_management_level
from ....shared.exceptions import MissingPermission
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("organisation.update")
class OrganisationUpdate(UpdateAction):
    """
    Action to update a organisation.
    """

    model = Organisation()
    schema = DefaultSchema(Organisation()).get_update_schema(
        optional_properties=[
            "name",
            "description",
            "legal_notice",
            "privacy_policy",
            "login_text",
            "theme",
            "custom_translations",
            #     "enable_electronic_voting", TODO
            "reset_password_verbose_errors",
        ]
    )

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        # check group A fields
        if any(
            [
                field in instance
                for field in [
                    "name",
                    "description",
                    "legal_notice",
                    "privacy_policy",
                    "login_text",
                    "theme",
                    "custom_translations",
                ]
            ]
        ) and not has_organisation_management_level(
            self.datastore,
            self.user_id,
            OrganisationManagementLevel.CAN_MANAGE_ORGANISATION,
        ):
            raise MissingPermission(OrganisationManagementLevel.CAN_MANAGE_ORGANISATION)

        # check group B fields
        if any(
            [
                field in instance
                for field in [
                    "enable_electronic_voting",
                    "reset_password_verbose_errors",
                ]
            ]
        ) and not has_organisation_management_level(
            self.datastore,
            self.user_id,
            OrganisationManagementLevel.SUPERADMIN,
        ):
            raise MissingPermission(OrganisationManagementLevel.SUPERADMIN)
