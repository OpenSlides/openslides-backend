from typing import Any, Dict

from ....models.models import ProjectorCountdown
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import FullQualifiedId
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projector_countdown.update")
class ProjectorCountdownUpdate(UpdateAction):
    """
    Action to update a projector countdown.
    """

    model = ProjectorCountdown()
    schema = DefaultSchema(ProjectorCountdown()).get_update_schema(
        required_properties=[],
        optional_properties=[
            "title",
            "description",
            "default_time",
            "countdown_time",
            "running",
        ],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        if instance.get("title"):
            self.check_title_unique(instance)
        return instance

    def check_title_unique(self, instance: Dict[str, Any]) -> None:
        projector_countdown = self.datastore.get(
            FullQualifiedId(self.model.collection, instance["id"]), ["meeting_id"]
        )
        title_filter = And(
            FilterOperator("meeting_id", "=", projector_countdown["meeting_id"]),
            FilterOperator("title", "=", instance["title"]),
        )
        if self.datastore.exists(self.model.collection, title_filter):
            raise ActionException("Title already exists in this meeting.")
