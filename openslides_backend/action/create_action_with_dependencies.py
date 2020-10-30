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
    """
    A list of actions which should be executed together with this create action.
    """

    def create_write_request_elements(
        self, dataset: DataSet
    ) -> Iterable[WriteRequestElement]:
        # Yield write request elements of this create action.
        yield from super().create_write_request_elements(dataset)

        for element in dataset["data"]:
            additional_relation_models = {
                FullQualifiedId(self.model.collection, element["new_id"]): element[
                    "instance"
                ],
            }
            for ActionClass in self.dependencies:
                special_check_method_name = "check_dependant_action_execution_" + str(
                    ActionClass.model.collection
                )
                check_method = getattr(
                    self,
                    special_check_method_name,
                    self.check_dependant_action_execution,
                )
                if not check_method(element, ActionClass):
                    continue
                special_payload_method_name = "get_dependent_action_payload_" + str(
                    ActionClass.model.collection
                )
                payload_method = getattr(
                    self, special_payload_method_name, self.get_dependent_action_payload
                )
                payload = [payload_method(element, ActionClass)]
                yield from self.execute_other_action(
                    ActionClass, payload, additional_relation_models
                )

    def check_dependant_action_execution(
        self, element: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> bool:
        """
        Check whether the dependency should be executed or not. Default is True.
        Override in subclass if necessary.
        """
        return True

    def get_dependent_action_payload(
        self, element: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> Dict[str, Any]:
        """
        Override in subclass to provide the correct payload for the dependencies.
        """
        raise NotImplementedError(
            "You have to implement get_dependent_action_payload for a "
            "CreateActionWithDependencies."
        )
