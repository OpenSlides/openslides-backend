import base64
import mimetypes
from typing import Any, Dict, Iterable, Union

from ....models.models import Resource
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.interfaces.event import EventType
from ....shared.interfaces.write_request_element import WriteRequestElement
from ....shared.patterns import FullQualifiedId
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionPayload, ActionResponseResultsElement


@register_action("resource.upload")
class MediafileUploadAction(CreateAction):
    """
    Action to upload a resourcefile.
    The token-field acts as unique key
    """

    model = Resource()
    schema = DefaultSchema(model).get_create_schema(
        required_properties=["token", "organisation_id"],
        additional_required_fields={
            "file": {"type": "string"},
            "filename": {"type": "string"},
        },
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        filename_ = instance.pop("filename")
        file_ = instance.pop("file")
        instance["mimetype"] = mimetypes.guess_type(filename_)[0]
        if instance["mimetype"] is None:
            raise ActionException(f"Cannot guess mimetype for {filename_}.")
        decoded_file = base64.b64decode(file_)
        instance["filesize"] = len(decoded_file)
        msg = self.upload_file(instance["id"], file_, instance["mimetype"])
        if msg:
            raise ActionException(msg)
        return instance

    def upload_file(self, id_: int, file_: str, mimetype: str) -> str:
        return self.media.upload_resource(file_, id_, mimetype)

    def get_updated_instances(self, payload: ActionPayload) -> ActionPayload:
        tokens = [instance["token"] for instance in payload]
        if len(tokens) != len(set(tokens)):
            raise ActionException(
                "It is not permitted to use the same token twice in a request."
            )

        for instance in payload:
            results = self.datastore.filter(
                self.model.collection,
                And(
                    FilterOperator("token", "=", instance["token"]),
                    FilterOperator("organisation_id", "=", instance["organisation_id"]),
                ),
            )
            if len(results) == 0:
                continue
            elif len(results) == 1:
                id = next(iter(results))
                instance["to_delete_id"] = id
            else:
                raise ActionException(
                    f'Database corrupt: The resource token has to be unique, but I found token "{instance["token"]}" {len(results)} times.'
                )

        return payload

    def create_write_request_elements(
        self, instance: Dict[str, Any]
    ) -> Iterable[Union[WriteRequestElement, ActionResponseResultsElement]]:
        to_delete_id = instance.pop("to_delete_id", None)
        if to_delete_id:
            fqid = FullQualifiedId(self.model.collection, to_delete_id)
            information = "Object deleted"
            yield self.build_write_request_element(EventType.Delete, fqid, information)
        yield from super().create_write_request_elements(instance)
