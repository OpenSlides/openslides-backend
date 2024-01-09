import base64
import mimetypes
from io import BytesIO
from time import time
from typing import Any, Dict, List, TypedDict, cast

import magic as python_magic
from pygments.lexers import guess_lexer, guess_lexer_for_filename
from pygments.util import ClassNotFound
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from ....models.models import Mediafile
from ....permissions.permissions import Permissions
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import KEYSEPARATOR
from ...action import original_instances
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .calculate_mixins import calculate_inherited_groups_helper_with_parent_id
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
            if "token" in instance and instance["token"] is None:
                raise ActionException("Token should not be None.")
            if "token" not in instance:
                continue
            tokens.append(instance.get("token"))
            results = self.datastore.filter(
                self.model.collection,
                And(
                    FilterOperator("token", "=", instance.get("token")),
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
                text = f'Database corrupt: The resource token has to be unique, but there are {len(results)} tokens "{instance.get("token")}".'
                self.logger.error(text)
                raise ActionException(text)
        if len(tokens) != len(set(tokens)):
            raise ActionException(
                "It is not permitted to use the same token twice in a request."
            )
        return action_data

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        """
        Looks for the mimetype of the file by name and content
        """
        instance = super().update_instance(instance)
        instance["create_timestamp"] = round(time())
        filename_ = instance.get("filename", "")
        file_ = instance.pop("file")  # get content of file
        decoded_file = base64.b64decode(file_)
        use_mimetype, _ = mimetypes.guess_type(filename_)
        if use_mimetype is None:
            raise ActionException(f"Cannot guess mimetype for {filename_}.")
        mc_mimetype = python_magic.from_buffer(decoded_file, mime=True)
        mismatched = True
        if use_mimetype == mc_mimetype:
            mismatched = False
        elif (
            use_mimetype.startswith("text") or use_mimetype == "application/json"
        ) and mc_mimetype.startswith("text"):
            """
            media types 'text' are assumed identical without checking media subtypes.
            Special: sometimes python_magic classifies json-content as 'text/plain'
            """
            mismatched = False
        elif mc_mimetype.startswith("text"):
            """
            The pygment library, specialized on syntax highlighting,
            helps on getting a wide range of text-mimetypes based on filename and content (try)
            or only content (except).
            Get text/plain as possible mimetype for file line.svg with guess_lexer, but has no svg-lexer
            """
            try:
                pyg_mimetypes = guess_lexer_for_filename(
                    filename_, decoded_file.decode()
                ).mimetypes
            except ClassNotFound:
                pyg_mimetypes = guess_lexer(decoded_file).mimetypes  # type: ignore
            if use_mimetype in pyg_mimetypes:
                mismatched = False
            else:
                mismatched = use_mimetype not in pyg_mimetypes
        else:
            """
            Getting possible extensions by python-magic given mimetypes by 2 ways:
            1. Get extensions from pythons integrated mimetypes-modul.
               Problem with font/sfnt: mimetypes has no extension for this mimetype
            2. Using python-magic to get the extensions from same code, which detected
               the mimetype. Get extensions, 'ttf' and 'otf', for mimetype font/sfnt following
               the Iana-specification
            """

            def check_extension(filename: str, extensions: List[str]) -> bool:
                return not any(
                    [filename_.endswith(extension) for extension in possible_extensions]
                )

            possible_extensions = mimetypes.guess_all_extensions(mc_mimetype)
            mismatched = check_extension(filename_, possible_extensions)
            if mismatched:
                possible_extensions = (
                    python_magic.Magic(extension=True)  # type: ignore
                    .from_buffer(decoded_file)
                    .split("/")
                )
                mismatched = check_extension(filename_, possible_extensions)

        if mismatched:
            raise ActionException(
                f"{filename_} does not have a file extension that matches the determined mimetype {mc_mimetype}."
            )
        instance["filesize"] = len(decoded_file)
        id_ = instance["id"]
        instance["mimetype"] = use_mimetype
        if instance["mimetype"] == "application/pdf":
            instance["pdf_information"] = self.get_pdf_information(decoded_file)
        collection, _ = self.get_owner_data(instance)
        if collection == "meeting":
            (
                instance["is_public"],
                instance["inherited_access_group_ids"],
            ) = calculate_inherited_groups_helper_with_parent_id(
                self.datastore,
                instance.get("access_group_ids"),
                instance.get("parent_id"),
            )
        else:
            instance["is_public"] = True
        self.media.upload_mediafile(file_, id_, cast(str, use_mimetype))
        return instance

    def get_pdf_information(self, file_bytes: bytes) -> PDFInformation:
        bytes_io = BytesIO(file_bytes)
        try:
            pdf = PdfReader(bytes_io)
            return {"pages": len(pdf.pages)}
        except PdfReadError:
            # File could be encrypted but not be detected by pypdf.
            return {
                "pages": 0,
                "encrypted": True,
            }
