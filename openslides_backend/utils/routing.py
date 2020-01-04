from typing import Any, Iterable

from werkzeug.routing import Map
from werkzeug.routing import Rule as WerkzeugRule
from werkzeug.routing import RuleFactory as WerkzeugRuleFactory

from .types import Environment


class Rule(WerkzeugRule):
    """
    Customized Rule to bind view function to the rule.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self.view = kwargs.pop("view")
        super().__init__(*args, **kwargs)


class RuleFactory(WerkzeugRuleFactory):
    """
    Customized RuleFactory to bind get_rules function to the factory.

    During initialization we bind the get_rules method from apps's views.
    """

    def __init__(self, environment: Environment) -> None:
        ...

    def get_rules(self, map: Map) -> Iterable[Rule]:
        """
        Use get_rules function from our app.
        """
        if not hasattr(self, "get_rules_func"):
            raise NotImplementedError
        return self.get_rules_func(map)  # type: ignore[attr-defined] # noqa E821
