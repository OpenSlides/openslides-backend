from typing import Any, Dict, Type

from ...models.base import Model
from ...shared.patterns import KEYSEPARATOR
from ..base import Action, BaseAction


class CreateActionWithListOfSpeakersMixin(BaseAction):
    """
    Mixin that can be used to create a list of speakers as a dependency.
    Just call the functions in the corresponding base functions.
    """

    model: Model

    def get_dependent_action_payload_list_of_speakers(
        self, element: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> Dict[str, Any]:
        return {
            "content_object_id": f"{str(self.model.collection)}{KEYSEPARATOR}{element['new_id']}",
        }
