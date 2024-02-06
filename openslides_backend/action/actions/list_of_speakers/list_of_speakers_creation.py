from typing import Any

from ....models.base import Model
from ....shared.patterns import KEYSEPARATOR
from ...action import Action


class CreateActionWithListOfSpeakersMixin(Action):
    """
    Mixin that can be used to create a list of speakers as a dependency.
    Just call the functions in the corresponding base functions.
    """

    model: Model

    def get_dependent_action_data_list_of_speakers(
        self, instance: dict[str, Any], CreateActionClass: type[Action]
    ) -> list[dict[str, Any]]:
        return [
            {
                "content_object_id": f"{str(self.model.collection)}{KEYSEPARATOR}{instance['id']}",
            }
        ]
