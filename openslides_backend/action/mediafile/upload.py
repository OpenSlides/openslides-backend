import mimetypes
from typing import Any, Dict

from ...models.models import Mediafile
from ...services.mediaservice.mediaservice import Mediaservice
from ...shared.exceptions import ActionException
from ...shared.patterns import FullQualifiedId
from ..base import ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action
from .calculate_mixins import MediafileCalculatedFieldsMixin


@register_action("mediafile.upload")
class MediafileUploadAction(CreateAction, MediafileCalculatedFieldsMixin):
    """
    Action to upload a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_create_schema(
        required_properties=["title", "meeting_id", "filename"],
        optional_properties=["access_group_ids", "parent_id"],
        additional_required_fields={"file": {"type": "string"}},
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Upload file into mediaservice.
        Check if parent is a directory.
        """
        if instance.get("parent_id"):
            parent_mediafile = self.database.get(
                FullQualifiedId(self.model.collection, instance["parent_id"]),
                [
                    "is_directory",
                    "has_inherited_access_groups",
                    "inherited_access_group_ids",
                ],
            )
            if parent_mediafile.get("is_directory") is not True:
                raise ActionException("Cannot have a non directory parent.")
            if instance.get("access_group_ids") is not None:
                (
                    instance["has_inherited_access_groups"],
                    instance["inherited_access_group_ids"],
                ) = self.calculate_inherited_groups(
                    10000,  # TODO remove this in future versions.
                    instance["access_group_ids"],
                    parent_mediafile.get("has_inherited_access_groups"),
                    parent_mediafile.get("inherited_access_group_ids"),
                )
        return instance

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        dataset = super().prepare_dataset(payload)
        for instance in dataset["data"]:
            file_ = instance["instance"].pop("file")
            id_ = instance["new_id"]
            mimetype = mimetypes.guess_type(instance["instance"]["filename"])[0]
            if mimetype is None:
                raise ActionException(
                    f"Cannot guess mimetype for {instance['instance']['filename']}."
                )
            self.upload_file(id_, file_, mimetype)
        return dataset

    def upload_file(self, id_: int, file_: str, mimetype: str) -> None:
        ms = Mediaservice()
        ms.upload(file_, id_, mimetype)
