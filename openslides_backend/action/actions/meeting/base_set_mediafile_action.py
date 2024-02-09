from typing import Any

from ....models.models import Meeting
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import KEYSEPARATOR, fqid_from_collection_and_id
from ....shared.schema import required_id_schema
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from .mixins import GetMeetingIdFromIdMixin


class BaseMeetingSetMediafileAction(UpdateAction, GetMeetingIdFromIdMixin):
    """
    Base action to set a speacial mediafile in a meeting.
    Subclass has to set `file_type` and `allowed_mimetypes`
    """

    file_type: str
    allowed_mimetypes: list[str]

    model = Meeting()
    schema = DefaultSchema(Meeting()).get_update_schema(
        additional_required_fields={
            "place": {"type": "string", "minLength": 1},
            "mediafile_id": required_id_schema,
        },
    )
    permission = Permissions.Meeting.CAN_MANAGE_LOGOS_AND_FONTS

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if not self.file_type or not self.allowed_mimetypes:
            raise NotImplementedError(
                "Subclass has to set file_type and allowed_mimetypes"
            )
        super().__init__(*args, **kwargs)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        """
        Checks is_directory and mimetype and sets logo.
        """
        mediafile = self.datastore.get(
            fqid_from_collection_and_id("mediafile", instance["mediafile_id"]),
            ["is_directory", "mimetype", "owner_id"],
        )
        self.check_owner(mediafile, instance)
        if mediafile.get("is_directory"):
            raise ActionException("Cannot set a directory.")
        if mediafile.get("mimetype") not in self.allowed_mimetypes:
            raise ActionException(
                f"Invalid mimetype: {mediafile.get('mimetype')}, allowed are {self.allowed_mimetypes}"
            )
        place = instance.pop("place")
        instance[f"{self.file_type}_{place}_id"] = instance.pop("mediafile_id")
        return instance

    def check_owner(self, mediafile: dict[str, Any], instance: dict[str, Any]) -> None:
        owner_id = mediafile["owner_id"]
        collection, id_ = owner_id.split(KEYSEPARATOR)
        if collection != "meeting":
            raise ActionException("Mediafile is not a meeting mediafile.")
        if int(id_) != instance["id"]:
            raise ActionException("Mediafile has to belong to this meeting..")
