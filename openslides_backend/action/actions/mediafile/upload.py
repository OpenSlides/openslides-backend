import base64
import mimetypes
from io import BytesIO
from time import time
from typing import Any, Dict, List, TypedDict

from PyPDF2 import PdfFileReader
from PyPDF2.utils import PdfReadError

from ....models.helper import calculate_inherited_groups_helper
from ....models.models import Mediafile
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import KEYSEPARATOR, FullQualifiedId
from ...action import original_instances
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .delete import MediafileDelete
from .mixins import MediafileMixin

PDFInformation = TypedDict(
    "PDFInformation",
    {
        "pages": int,
        "encrypted": bool,
    },
    total=False,
)


@register_action("mediafile.upload")
class MediafileUploadAction(MediafileMixin, CreateAction):
    """
    Action to upload a mediafile.
    """

    model = Mediafile()
    schema = DefaultSchema(Mediafile()).get_create_schema(
        required_properties=["title", "owner_id", "filename"],
        optional_properties=["token", "access_group_ids", "parent_id"],
        additional_required_fields={"file": {"type": "string"}},
    )
    permission = Permissions.Mediafile.CAN_MANAGE

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        tokens: List[Any] = []
        for instance in action_data:
            collection, _ = self.get_owner_data(instance)
            if collection != "organization":
                continue
            tokens.append(instance.get("token"))
            results = self.datastore.filter(
                self.model.collection,
                And(
                    FilterOperator("token", "=", instance["token"]),
                    FilterOperator(
                        "owner_id", "=", "organization" + KEYSEPARATOR + "1"
                    ),
                ),
                ["id"],
            )
            if len(results) == 0:
                continue
            elif len(results) == 1:
                id = next(iter(results))
                self.execute_other_action(MediafileDelete, [{"id": id}])
            else:
                text = f'Database corrupt: The resource token has to be unique, but there are {len(results)} tokens "{instance["token"]}".'
                self.logger.error(text)
                raise ActionException(text)
        if len(tokens) != len(set(tokens)):
            raise ActionException(
                "It is not permitted to use the same token twice in a request."
            )
        return action_data

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().update_instance(instance)
        instance["create_timestamp"] = round(time())
        filename_ = instance.get("filename", "")
        file_ = instance.pop("file")
        instance["mimetype"] = mimetypes.guess_type(filename_)[0]
        if instance["mimetype"] is None:
            raise ActionException(f"Cannot guess mimetype for {filename_}.")
        decoded_file = base64.b64decode(file_)
        instance["filesize"] = len(decoded_file)
        id_ = instance["id"]
        mimetype_ = instance["mimetype"]
        if instance["mimetype"] == "application/pdf":
            instance["pdf_information"] = self.get_pdf_information(decoded_file)
        collection, _ = self.get_owner_data(instance)
        if collection == "meeting":
            instance = self.update_access_fields(instance)
        self.media.upload_mediafile(file_, id_, mimetype_)
        return instance

    def update_access_fields(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if instance.get("parent_id"):
            parent = self.datastore.get(
                FullQualifiedId(self.model.collection, instance["parent_id"]),
                [
                    "is_public",
                    "inherited_access_group_ids",
                ],
            )
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
