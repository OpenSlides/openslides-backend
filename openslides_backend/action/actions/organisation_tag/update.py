from ....models.models import OrganisationTag
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("organisation_tag.update")
class OrganisationTagUpdate(UpdateAction):
    """
    Action to update an organisation tag.
    """

    model = OrganisationTag()
    schema = DefaultSchema(OrganisationTag()).get_update_schema(
        optional_properties=["name", "color"]
    )
