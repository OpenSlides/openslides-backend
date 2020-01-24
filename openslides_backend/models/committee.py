from ..shared.patterns import Collection
from . import fields
from .base import Model


class OrganisationField(fields.ForeignKeyField):
    """
    Special field for foreign key to organisation model. We support only one
    organisation (with id 1) at the moment.
    """

    def get_schema(self) -> fields.Schema:
        schema = super().get_schema()
        schema["maximun"] = 1
        return schema


class Committee(Model):
    """
    Model for committees.
    """

    collection = Collection("committee")
    verbose_name = "committee"

    # TODO: Make to and related_name in relation fields optional.

    id = fields.IdField(description="An integer. The id of the committee.")
    organisation_id = OrganisationField(
        description="An integer. The id of the organisation of the committee.",
        to="organisation",
        related_name="committee_ids",
    )
    title = fields.RequiredCharField(
        description="A string. The title or headline of the committee."
    )
