from typing import Any, Dict, List, Type

from ...shared.patterns import FullQualifiedId
from ..action import Action
from ..generics.create import CreateAction


class CreateActionWithDependencies(CreateAction):
    """
    A CreateAction which has dependant actions which should be executed for each item.
    """

    dependencies: List[Type[Action]]
    """
    A list of actions which should be executed together with this create action.
    """

    def base_update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        instance = super().base_update_instance(instance)
        additional_relation_models = {
            FullQualifiedId(self.model.collection, instance["id"]): instance,
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
            if not check_method(instance, ActionClass):
                continue
            special_action_data_method_name = "get_dependent_action_data_" + str(
                ActionClass.model.collection
            )
            action_data_method = getattr(
                self, special_action_data_method_name, self.get_dependent_action_data
            )
            action_data = action_data_method(instance, ActionClass)
            self.execute_other_action(
                ActionClass, action_data, additional_relation_models
            )
        return instance

    def check_dependant_action_execution(
        self, instance: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> bool:
        """
        Check whether the dependency should be executed or not. Default is True.
        Override in subclass if necessary.
        """
        return True

    def get_dependent_action_data(
        self, instance: Dict[str, Any], CreateActionClass: Type[Action]
    ) -> List[Dict[str, Any]]:
        """
        Override in subclass to provide the correct action data for the dependencies.
        """
        raise NotImplementedError(
            "You have to implement get_dependent_action_data for a "
            "CreateActionWithDependencies."
        )
