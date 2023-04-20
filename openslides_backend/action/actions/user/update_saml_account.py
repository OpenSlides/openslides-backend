from typing import Any, Dict

from ....models.models import User
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator
from ...generics.update import UpdateAction
from ...util.action_type import ActionType
from ...util.default_schema import DefaultSchema
from ...util.register import register_action


@register_action("user.update_saml_account", action_type=ActionType.STACK_INTERNAL)
class UserUpdateSamlAccount(UpdateAction):
    """
    Internal action to update a saml account.
    It should be called from the auth service.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        required_properties=["saml_id"],
        optional_properties=[
            "title",
            "first_name",
            "last_name",
            "email",
            "gender",
            "pronoun",
            "is_active",
            "is_physical_person",
        ],
        title="update saml account schema",
    )
    skip_archived_meeting_check = True

    def update_instance(self, instance: Dict[str, Any]) -> Dict[str, Any]:
        filter_ = FilterOperator("saml_id", "=", instance.pop("saml_id"))
        users = self.datastore.filter("user", filter_, ["id"])
        if len(users) != 1:
            raise ActionException("Wrong saml_id.")
        instance["id"] = next(iter(users.values()))["id"]
        return instance

    def check_permissions(self, instance: Dict[str, Any]) -> None:
        pass
