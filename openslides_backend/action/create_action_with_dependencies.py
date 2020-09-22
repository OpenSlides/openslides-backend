from typing import Any, Dict, Iterable, List, Type

from ..shared.interfaces import WriteRequestElement
from ..shared.patterns import FullQualifiedId
from .base import Action, DataSet
from .generics import CreateAction


class CreateActionWithDependencies(CreateAction):
    """
    A CreateAction which has dependant actions which should be executed for each item.
    """

    dependencies: List[Type[Action]]
    """ A list of Actions which should be executed together with this create action. """

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        # yield write elements of this create action
        yield from super().create_write_request_elements(dataset)

        for element in dataset["data"]:
            # merge additional_relation_models for possible nesting
            additional_relation_models = {
                **self.additional_relation_models,
                FullQualifiedId(self.model.collection, element["new_id"]): element[
                    "instance"
                ],
            }
            for ActionClass in self.dependencies:
                if not self.check_dependant_action_execution(element, ActionClass):
                    continue
                action = ActionClass(
                    self.permission, self.database, additional_relation_models,
                )
                payload = [self.get_dependent_action_payload(element, ActionClass)]
                yield from action.perform(payload, self.user_id)

    def check_dependant_action_execution(
        self, element: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> bool:
        """ Check whether the dependency should be executed or not. Override in subclass if needed. """
        return True

    def get_dependent_action_payload(
        self, element: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> Dict[str, Any]:
        """ Override in subclass to provide the correct payload for the dependencies. """
        raise NotImplementedError(
            "You have to implement get_dependent_action_payload for a CreateActionWithDependencies"
        )
