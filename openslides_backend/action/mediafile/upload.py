import base64
import mimetypes
from io import BytesIO
from time import time
from typing import Any, Dict, TypedDict

from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError

from ...models.models import Mediafile
from ...shared.exceptions import ActionException
from ...shared.patterns import FullQualifiedId
from ..base import ActionPayload, DataSet
from ..default_schema import DefaultSchema
from ..generics import CreateAction
from ..register import register_action
from .calculate_mixins import MediafileCalculatedFieldsMixin

PDFInformation = TypedDict(
    "PDFInformation",
    {
        "pages": int,
        "encrypted": bool,
    },
    total=False,
)


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
        instance["create_timestamp"] = time()
        instance["mimetype"] = mimetypes.guess_type(instance["filename"])[0]
        if instance["mimetype"] is None:
            raise ActionException(f"Cannot guess mimetype for {instance['filename']}.")
        decoded_file = base64.b64decode(instance["file"])
        instance["filesize"] = len(decoded_file)
        if instance["mimetype"] == "application/pdf":
            instance["pdf_information"] = self.get_pdf_information(decoded_file)

        if instance.get("parent_id"):
            parent_mediafile = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["parent_id"]),
                [
                    "is_directory",
                    "is_public",
                    "inherited_access_group_ids",
                ],
            )
            if parent_mediafile.get("is_directory") is not True:
                raise ActionException("Cannot have a non directory parent.")
            if instance.get("access_group_ids") is not None:
                (
                    instance["is_public"],
                    instance["inherited_access_group_ids"],
                ) = self.calculate_inherited_groups(
                    instance["access_group_ids"],
                    parent_mediafile.get("is_public"),
                    parent_mediafile.get("inherited_access_group_ids"),
                )
        return instance

    def prepare_dataset(self, payload: ActionPayload) -> DataSet:
        dataset = super().prepare_dataset(payload)
        for instance in dataset["data"]:
            file_ = instance["instance"].pop("file")
            id_ = instance["new_id"]
            mimetype_ = instance["instance"]["mimetype"]
            self.upload_file(id_, file_, mimetype_)
        return dataset

    def upload_file(self, id_: int, file_: str, mimetype: str) -> None:
        self.media.upload(file_, id_, mimetype)

    def get_pdf_information(self, file_bytes: bytes) -> PDFInformation:
        bytes_io = BytesIO(file_bytes)
        try:
            pdf = PdfFileReader(bytes_io)
            return {"pages": pdf.getNumPages()}
        except PdfReadError:
            # File could be encrypted but not be detected by PyPDF.
            return {
                "pages": 0,
                "encrypted": True,
            }
