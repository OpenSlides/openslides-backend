import base64
import mimetypes
from typing import Any, Dict

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import Resource
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ...action import original_instances
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .delete import ResourceDelete
from .mixins import PermissionMixin


@register_action("resource.upload")
class ResourceUploadAction(PermissionMixin, CreateAction, CheckForArchivedMeetingMixin):
    """
    Action to upload a resourcefile.
    The token-field acts as unique key
    """

    model = Resource()
    schema = DefaultSchema(model).get_create_schema(
        required_properties=["token", "organization_id"],
        additional_required_fields={
            "file": {"type": "string"},
            "filename": {"type": "string"},
        },
    )
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        filename_ = instance.pop("filename")
        file_ = instance.pop("file")
        instance["mimetype"] = mimetypes.guess_type(filename_)[0]
        if instance["mimetype"] is None:
            raise ActionException(f"Cannot guess mimetype for {filename_}.")
        decoded_file = base64.b64decode(file_)
        instance["filesize"] = len(decoded_file)
        id_ = instance["id"]
        mimetype_ = instance["mimetype"]
        self.media.upload_resource(file_, id_, mimetype_)
        return instance

    @original_instances
    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        tokens = [instance["token"] for instance in action_data]
        if len(tokens) != len(set(tokens)):
            raise ActionException(
                "It is not permitted to use the same token twice in a request."
            )

        for instance in action_data:
            results = self.datastore.filter(
                self.model.collection,
                And(
                    FilterOperator("token", "=", instance["token"]),
                    FilterOperator("organization_id", "=", instance["organization_id"]),
                ),
                ["id"],
            )
            if len(results) == 0:
                continue
            elif len(results) == 1:
                id = next(iter(results))
                self.execute_other_action(ResourceDelete, [{"id": id}])
            else:
                text = f'Database corrupt: The resource token has to be unique, but there are {len(results)} tokens "{instance["token"]}".'
                self.logger.error(text)
                raise ActionException(text)

        return action_data
