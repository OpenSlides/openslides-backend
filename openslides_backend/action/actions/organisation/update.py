from ....models.models import Organisation
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
            "reset_password_verbose_errors",
        ]
    )
