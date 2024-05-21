from typing import Any

from openslides_backend.services.datastore.interface import PartialModel

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....services.datastore.interface import DatastoreService
from ....shared.exceptions import ActionException
from ....shared.filters import FilterOperator, Or
from ....shared.interfaces.env import Env
from ....shared.interfaces.logging import LoggingModule
from ....shared.interfaces.services import Services
from ....shared.patterns import Collection, fqid_from_collection_and_id
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...relations.relation_manager import RelationManager
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from .create import UserCreate
from .delete import UserDelete
from .merge_mixins import MeetingUserMergeMixin
from .update import UserUpdate


@register_action("user.merge_together")
class UserMergeTogether(
    MeetingUserMergeMixin, UpdateAction  # , CheckForArchivedMeetingMixin
):
    """
    Action to merge users together.
    """

    model = User()
    schema = DefaultSchema(User()).get_default_schema(
        required_properties=["id"],
        optional_properties=[
            "username",
            "title",
            "first_name",
            "last_name",
            "is_active",
            "is_physical_person",
            "default_password",
            "gender",
            "email",
            "default_vote_weight",
        ],
        additional_required_fields={
            "user_ids": {
                "description": "A list of user ids to merge into a user.",
                **id_list_schema,
            },
        },
    )
    permission = permission = OrganizationManagementLevel.CAN_MANAGE_USERS

    def __init__(
        self,
        services: Services,
        datastore: DatastoreService,
        relation_manager: RelationManager,
        logging: LoggingModule,
        env: Env,
        skip_archived_meeting_check: bool | None = None,
        use_meeting_ids_for_archived_meeting_check: bool | None = None,
    ) -> None:
        super().__init__(
            services,
            datastore,
            relation_manager,
            logging,
            env,
            skip_archived_meeting_check,
            use_meeting_ids_for_archived_meeting_check,
        )
        self.add_collection_field_groups(
            User,
            {"create": UserCreate, "update": UserUpdate, "delete": UserDelete},
            {
                "ignore": [
                    "password",
                    "default_password",
                    "organization_id",
                ],
                "highest": [
                    "is_active",
                    "is_physical_person",
                    "can_change_own_password",
                    "last_email_sent",
                    "last_login",
                ],
                "error": [
                    "is_demo_user",
                    "forwarding_committee_ids",
                ],
                "priority": [
                    "username",
                    "saml_id",
                    "pronoun",
                    "title",
                    "first_name",
                    "last_name",
                    "gender",
                    "email",
                    "default_vote_weight",
                ],
                "merge": [
                    "is_present_in_meeting_ids",
                    "committee_ids",
                    "committee_management_ids",
                    "meeting_ids",
                ],
                "deep_merge": {
                    "meeting_user_ids": "meeting_user",
                    "poll_candidate_ids": "poll_candidate",
                },
                "special_function": [
                    "organization_management_level",
                    "option_ids",  # throw error if conflict on same poll, else merge
                    "poll_voted_ids",  # throw error if conflict on same poll, else merge
                    "vote_ids",  # throw error if conflict on same poll, else merge
                    "delegated_vote_ids",  # throw error if conflict on same poll, else merge
                ],
            },
        )
        self.check_collection_field_groups()

    def prefetch(self, action_data: ActionData) -> None:
        self.mass_prefetch_for_merge(
            {
                "user": [
                    id_
                    for instance in action_data
                    for id_ in {instance.get("id"), *instance.get("user_ids", [])}
                    if id_
                ]
            }
        )

    def get_updated_instances(self, action_data: ActionData) -> ActionData:
        user_ids = [
            id_ for instance in action_data for id_ in set(instance.get("user_ids", []))
        ]
        if len(user_ids) != len(set(user_ids)):
            raise ActionException(
                "Users cannot be merged into multiple different users at the same time"
            )
        return super().get_updated_instances(action_data)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        # TODO: Is this stuff necessary
        user_data, meeting_users = self._get_user_data(instance["id"])
        meeting_user_data_by_meeting_id: dict[int, PartialModel] = {}
        for meeting_user in meeting_users.values():
            if meeting_user_data_by_meeting_id.get(
                meeting_id := meeting_user["meeting_id"]
            ):
                raise ActionException(
                    f"Primary meeting user has multiple meeting_users for meeting {meeting_id}"
                )
            meeting_user_data_by_meeting_id[meeting_id] = meeting_user
        if self.user_id in instance["user_ids"]:
            raise ActionException("Operator may not merge himself into others.")

        models = self.get_merge_by_rank_models(
            "user", [instance["id"], *instance["user_ids"]]
        )
        into, other_models = self.split_merge_by_rank_models(
            instance["id"], instance["user_ids"], models
        )
        result = self.merge_by_rank("user", into, other_models, instance)
        return result

    def get_merge_comparison_hash(
        self, collection: Collection, model: PartialModel
    ) -> int | str:
        match collection:
            case "meeting_user":
                return model["meeting_id"]
            case _:
                # TODO: Add other merge model fields
                return super().get_merge_comparison_hash(collection, model)

    def _get_user_data(
        self, user_id: int
    ) -> tuple[PartialModel, dict[int, PartialModel]]:
        user = self.datastore.get(
            fqid_from_collection_and_id("user", user_id),
            self._all_collection_fields["user"].copy(),
        )
        return (
            user,
            self.datastore.filter(
                "meeting_user",
                FilterOperator("user_id", "=", user_id),
                self._all_collection_fields["meeting_user"].copy(),
            ),
        )

    def get_meeting_ids(self, instance: dict[str, Any]) -> list[int]:
        meeting_users = self.datastore.filter(
            "meeting_user",
            Or(
                FilterOperator("user_id", "=", user_id)
                for user_id in [instance["id"], *instance["user_ids"]]
            ),
            ["meeting_id"],
        ).values()
        return list({m["meeting_id"] for m in meeting_users})
