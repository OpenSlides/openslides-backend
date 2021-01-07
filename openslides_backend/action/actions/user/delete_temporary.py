from typing import Any, Dict

from ....models.models import User
from ...generics.delete import DeleteAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from .check_temporary_mixin import CheckTemporaryMixin


@register_action("user.delete_temporary")
class UserDeleteTemporary(CheckTemporaryMixin, DeleteAction):
    """
    Action to delete a user.
    """

    model = User()
    schema = DefaultSchema(User()).get_delete_schema()

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        self.check_for_temporary(instance)
        return instance
