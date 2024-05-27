from typing import Any

from openslides_backend.services.datastore.interface import PartialModel

from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
from ....shared.exceptions import ActionException, BadCodingException
from ....shared.filters import And, FilterOperator, Or
from ....shared.interfaces.env import Env
from ....shared.interfaces.logging import LoggingModule
from ....shared.interfaces.services import Services
from ....shared.patterns import Collection, CollectionField, fqid_from_collection_and_id
from ....shared.schema import id_list_schema
from ...generics.update import UpdateAction
from ...relations.relation_manager import RelationManager
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..meeting_user.update import MeetingUserUpdate
from .base_merge_mixin import MergeUpdateOperations
from .delete import UserDelete
from .merge_mixins import MeetingUserMergeMixin
from .update import UserUpdate
from .user_mixins import UserMixin


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
            {
                "ignore": [
                    "password",
                    "default_password",
                    "organization_id",
                    "last_email_sent",
                    "last_login",
                    "committee_ids",
                    "meeting_ids",
                ],
                "highest": [
                    "is_active",
                    "is_physical_person",
                    "can_change_own_password",
                ],
                "error": [
                    "is_demo_user",
                    "forwarding_committee_ids",
                ],
                "priority": [
                    "username",
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
                    "committee_management_ids",
                    "option_ids",  # throw error if conflict on same poll
                    "poll_voted_ids",  # throw error if conflict on same poll
                    "vote_ids",  # throw error if conflict on same poll
                    "delegated_vote_ids",  # throw error if conflict on same poll
                ],
                "deep_merge": {
                    "poll_candidate_ids": "poll_candidate",
                },
                "deep_create_merge": {
                    "meeting_user_ids": "meeting_user",
                },
                "special_function": [
                    "organization_management_level",
                    "saml_id",  # error if set on secondary users, otherwise ignore the field
                ],
                "require_equality": ["member_number"],
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
        update_operations: dict[Collection, MergeUpdateOperations] = {
            coll: {"create": [], "update": [], "delete": []}
            for coll in self._collection_field_groups
        }
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

        self.check_polls(into, other_models)

        update_operations["user"]["update"].append(
            self.merge_by_rank("user", into, other_models, instance, update_operations)
        )
        self.call_other_actions(update_operations)
        return {"id": into["id"]}

    def call_other_actions(
        self, update_operations: dict[Collection, MergeUpdateOperations]
    ) -> None:
        if len(update_operations["user"]["update"]) != 1:
            raise BadCodingException("Calculated wrong amount of user payloads")
        main_user_payload = update_operations["user"]["update"][0]
        user_id = main_user_payload["id"]
        if len(
            update_payloads := [
                *update_operations["meeting_user"]["update"],
                *update_operations["meeting_user"]["create"],
            ]
        ):
            main_user_payload.update(
                {
                    "id": user_id,
                    "meeting_id": update_payloads[0]["meeting_id"],
                    **{
                        field: update_payloads[0].pop(field)
                        for field in UserMixin.transfer_field_list
                        if field in update_payloads[0]
                    },
                }
            )
            for payload_index in range(1, len(update_payloads)):
                current = update_payloads[payload_index]
                update_operations["user"]["update"].append(
                    {
                        "id": user_id,
                        "meeting_id": current["meeting_id"],
                        **{
                            field: current.pop(field)
                            for field in UserMixin.transfer_field_list
                            if field in current
                        },
                    }
                )
            self.execute_other_action(UserUpdate, update_operations["user"]["update"])

            meeting_user_update_payloads = [
                payload
                for payload in update_operations["meeting_user"]["update"]
                if len(payload) > 1
            ]
            new_meeting_ids = [
                m_user["meeting_id"]
                for m_user in update_operations["meeting_user"]["create"]
            ]
            new_meeting_users = self.datastore.filter(
                "meeting_user",
                And(
                    FilterOperator("user_id", "=", user_id),
                    Or(
                        FilterOperator("meeting_id", "=", meeting_id)
                        for meeting_id in new_meeting_ids
                    ),
                ),
                ["meeting_id"],
            )
            meeting_user_ids_by_meeting_ids = {
                m_user["meeting_id"]: id_ for id_, m_user in new_meeting_users.items()
            }
            for payload in update_operations["meeting_user"]["create"]:
                if len(payload):
                    payload["id"] = meeting_user_ids_by_meeting_ids[
                        payload["meeting_id"]
                    ]
                    meeting_user_update_payloads.append(payload)
            if len(meeting_user_update_payloads):
                for payload in meeting_user_update_payloads:
                    payload.pop("meeting_id")
                self.execute_other_action(
                    MeetingUserUpdate, meeting_user_update_payloads
                )

            if len(update_operations["user"]["delete"]):
                self.execute_other_action(
                    UserDelete,
                    [{"id": id_} for id_ in update_operations["user"]["delete"]],
                    UserDelete.skip_archived_meeting_check,
                )

    def check_polls(self, into: PartialModel, other_models: list[PartialModel]) -> None:
        poll_ids_per_user_id: dict[int, set[int]] = {}
        for model in [into, *other_models]:
            vote_data = self.datastore.get_many(
                [
                    GetManyRequest(
                        "vote",
                        list(
                            {
                                id_
                                for id_ in [
                                    *model.get("vote_ids", []),
                                    *model.get("delegated_vote_ids", []),
                                ]
                            }
                        ),
                        ["option_id"],
                    )
                ]
            )["vote"]
            poll_ids_per_user_id[model["id"]] = {
                option["poll_id"]
                for option in self.datastore.get_many(
                    [
                        GetManyRequest(
                            "option",
                            list(
                                {
                                    id_
                                    for id_ in [
                                        *model.get("option_ids", []),
                                        *[
                                            vote["option_id"]
                                            for vote in vote_data.values()
                                            if vote.get("option_id")
                                        ],
                                    ]
                                }
                            ),
                            ["poll_id"],
                        )
                    ]
                )["option"].values()
                if option.get("poll_id")
            }
            poll_conflicts = {
                poll_id
                for id1 in poll_ids_per_user_id
                for id2 in poll_ids_per_user_id
                for poll_id in poll_ids_per_user_id[id1].intersection(
                    poll_ids_per_user_id[id2]
                )
                if id1 != id2
            }
            if len(poll_conflicts):
                raise ActionException(
                    f"Cannot carry out merge into user/{into['id']}, because among the selected users multiple voted in poll(s) {', '.join([str(id_) for id_ in poll_conflicts])}"
                )

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

    def handle_special_field(
        self,
        collection: Collection,
        field: CollectionField,
        into_: PartialModel,
        ranked_others: list[PartialModel],
    ) -> Any | None:
        if collection == "user":
            match field:
                case "organization_management_level":
                    all_omls = [
                        OrganizationManagementLevel(oml)
                        for model in [into_, *ranked_others]
                        if (oml := model.get(field))
                    ]
                    if len(all_omls) == 0:
                        return None
                    return max(all_omls)
                case "saml_id":
                    # error if set on secondary users, otherwise ignore the field
                    if any([field in model for model in ranked_others]):
                        raise ActionException(
                            f"Merge of user/{into_['id']}: Saml_id may not exist on any user except target."
                        )
                    return None
        return super().handle_special_field(collection, field, into_, ranked_others)
