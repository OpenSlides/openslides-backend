from typing import Any, Dict

from ....models.models import ProjectorCountdown
from ....shared.exceptions import ActionException
from ....shared.filters import And, FilterOperator
from ....shared.patterns import Collection, FullQualifiedId
from ...generics.create import CreateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("projector_countdown.create")
class ProjectorCountdownCreate(CreateAction):
    """
    Action to create a projector countdown.
    """

    model = ProjectorCountdown()
    schema = DefaultSchema(ProjectorCountdown()).get_create_schema(
        required_properties=["meeting_id", "title"],
        optional_properties=["description", "default_time"],
    )

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        self.check_title_unique(instance)

        # set default_time if needed and countdown_time
        print(instance.get("default_time"))
        if not instance.get("default_time"):
            meeting = self.datastore.get(
                FullQualifiedId(Collection("meeting"), instance["meeting_id"]),
                ["projector_countdown_default_time"],
            )
            instance["default_time"] = meeting.get("projector_countdown_default_time")
        instance["countdown_time"] = instance["default_time"]
        return instance

    def check_title_unique(self, instance: Dict[str, Any]) -> None:
        title_filter = And(
            FilterOperator("meeting_id", "=", instance["meeting_id"]),
            FilterOperator("title", "=", instance["title"]),
        )
        if self.datastore.exists(self.model.collection, title_filter):
            raise ActionException("Title already exists in this meeting.")
