from ..action import Action
from ..ddaction import DDAction

# Map of all actions with their respective classes. Is filled in ../actions/__init__.py to
# prevent circular imports.
# At least one action has to be imported to make sure that the map is filled.
actions_map: dict[str, type[Action] | type[DDAction]] = {}
