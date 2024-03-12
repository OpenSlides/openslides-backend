from typing import Any

from ..action import Action
from ..generics.create import CreateAction


class CreateActionWithDependencies(CreateAction):
    """
    A CreateAction which has dependant actions which should be executed for each item.
    """

    dependencies: list[type[Action]]
    """
    A list of actions which should be executed together with this create action.
    """

    def base_update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().base_update_instance(instance)
        self.apply_instance(instance)
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
            self.execute_other_action(ActionClass, action_data)
        return instance

    def check_dependant_action_execution(
        self, instance: dict[str, Any], CreateActionClass: type[Action]
    ) -> bool:
        """
        Check whether the dependency should be executed or not. Default is True.
        Override in subclass if necessary.
        """
        return True

    def get_dependent_action_data(
        self, instance: dict[str, Any], CreateActionClass: type[Action]
    ) -> list[dict[str, Any]]:
        """
        Override in subclass to provide the correct action data for the dependencies.
        """
        raise NotImplementedError(
            "You have to implement get_dependent_action_data for a "
            "CreateActionWithDependencies."
        )
