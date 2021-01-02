from typing import Any, Dict, List

from ....models.models import Meeting
from ....shared.exceptions import ActionException
from ....shared.patterns import Collection, FullQualifiedId
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema


class BaseMeetingSetMediafileAction(UpdateAction):
    """
    Base action to set a speacial mediafile in a meeting.
    Subclass has to set `field` and `allowed_mimetypes`
    """

    field: str
    allowed_mimetypes: List[str]

    model = Meeting()
    schema = DefaultSchema(Meeting()).get_update_schema(
        additional_required_fields={
            "place": {"type": "string", "minLength": 1},
            "mediafile_id": required_id_schema,
        },
    )
    permission_description = "meeting.can_manage_logos_and_fonts"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if not self.field or not self.allowed_mimetypes:
            raise NotImplementedError("Subclass has to set field and allowed_mimetypes")
        super().__init__(*args, **kwargs)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Checks is_directory and mimetype and sets logo.
        """
        mediafile = self.datastore.get(
            FullQualifiedId(Collection("mediafile"), instance["mediafile_id"]),
            ["is_directory", "mimetype", "meeting_id"],
        )
        if mediafile.get("meeting_id") != instance["id"]:
            raise ActionException("Mediafile has to belong to this meeting.")
        if mediafile.get("is_directory"):
            raise ActionException("Cannot set a directory.")
        if mediafile.get("mimetype") not in self.allowed_mimetypes:
            raise ActionException(
                f"Invalid mimetype: {mediafile.get('mimetype')}, allowed are {self.allowed_mimetypes}"
            )

        structured_field = self.field.replace("$", "$" + instance.pop("place"))
        instance[structured_field] = instance.pop("mediafile_id")
        return instance
