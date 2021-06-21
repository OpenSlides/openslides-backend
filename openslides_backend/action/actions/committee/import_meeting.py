from typing import Any, Dict, Optional, Tuple

from ....models.models import Committee
from ....shared.exceptions import ActionException, MissingPermission
from ....shared.interfaces.write_request import WriteRequest
from ...action import Action
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData, ActionResults


@register_action("committee.import_meeting")
class CommitteeImportMeeting(Action):
    """
    Action to import a meeting.
    """

    model = Committee()
    schema = DefaultSchema(Committee()).get_update_schema(
        additional_required_fields={"meeting_json": {"type": "object"}}
    )

    def perform(
        self, action_data: ActionData, user_id: int, internal: bool = False
    ) -> Tuple[Optional[WriteRequest], Optional[ActionResults]]:
        """
        Simplified entrypoint to perform the action.
        """
        self.user_id = user_id
        self.index = 0
        for instance in action_data:
            self.validate_instance(instance)
            try:
                self.check_permissions(instance)
            except MissingPermission as e:
                msg = f"You are not allowed to perform action {self.name}."
                e.message = msg + " " + e.message
                raise e
            self.index += 1
        self.index = -1

        instances = self.get_updated_instances(action_data)
        for instance in instances:
            instance = self.base_update_instance(instance)

            write_request = self.create_write_requests(instance)
            self.write_requests.extend(write_request)

        final_write_request = self.process_write_requests()
        return (final_write_request, None)

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        meeting_json = instance["meeting_json"]
        if not len(meeting_json.get("meeting", [])) == 1:
            raise ActionException("Need exact one meeting in meeting collection.")
        shall_be_empty = ("organization", "organization_tag", "committee", "resource")
        for collection in shall_be_empty:
            if meeting_json.get(collection):
                raise ActionException(f"{collection} must be empty.")

        for user in meeting_json.get("user", []):
            if not user["password"] == "":
                raise ActionException("User password must be an empty string.")
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        return
