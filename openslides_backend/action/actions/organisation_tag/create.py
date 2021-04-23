from ....models.models import OrganisationTag
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("organisation_tag.create")
class OrganisationTagCreate(CreateAction):
    """
    Action to create an organisation tag.
    """

    model = OrganisationTag()
    schema = DefaultSchema(OrganisationTag()).get_create_schema(
        required_properties=["name", "color"]
    )
