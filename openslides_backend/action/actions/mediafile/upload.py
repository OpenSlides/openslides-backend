import base64
import mimetypes
from io import BytesIO
from time import time
from typing import Any, Dict, TypedDict

from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError

from ....models.helper import calculate_inherited_groups_helper
from ....models.models import Mediafile
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.patterns import FullQualifiedId
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .permission_mixin import MediafilePermissionMixin

PDFInformation = TypedDict(
    "PDFInformation",
    {
        "pages": int,
        "encrypted": bool,
    },
    total=False,
)


@register_action("mediafile.upload")
class MediafileUploadAction(MediafilePermissionMixin, CreateAction):
    """
    Action to upload a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_create_schema(
        required_properties=["title", "owner_id", "filename"],
        optional_properties=["access_group_ids", "parent_id"],
        additional_required_fields={"file": {"type": "string"}},
    )
    permission = Permissions.Mediafile.CAN_MANAGE
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance["create_timestamp"] = round(time())
        instance["mimetype"] = mimetypes.guess_type(instance["filename"])[0]
        if instance["mimetype"] is None:
            raise ActionException(f"Cannot guess mimetype for {instance['filename']}.")
        decoded_file = base64.b64decode(instance["file"])
        instance["filesize"] = len(decoded_file)
        if instance["mimetype"] == "application/pdf":
            instance["pdf_information"] = self.get_pdf_information(decoded_file)

        if instance.get("parent_id"):
            parent = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["parent_id"]),
                [
                    "is_directory",
                    "is_public",
                    "inherited_access_group_ids",
                ],
            )
            if parent.get("is_directory") is not True:
                raise ActionException("Cannot have a non-directory parent.")

            (
                instance["is_public"],
                instance["inherited_access_group_ids"],
            ) = calculate_inherited_groups_helper(
                instance.get("access_group_ids"),
                parent.get("is_public"),
                parent.get("inherited_access_group_ids"),
            )
        else:
            instance["is_public"] = not bool(instance.get("access_group_ids"))
            instance["inherited_access_group_ids"] = instance.get("access_group_ids")
        file_ = instance.pop("file")
        id_ = instance["id"]
        mimetype_ = instance["mimetype"]
        self.media.upload_mediafile(file_, id_, mimetype_)
        return instance

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
