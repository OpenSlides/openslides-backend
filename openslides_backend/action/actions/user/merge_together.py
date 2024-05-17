from typing import Any, TypedDict, cast

from openslides_backend.services.datastore.interface import PartialModel

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import MeetingUser, User
from ....permissions.management_levels import OrganizationManagementLevel
from ....services.datastore.commands import GetManyRequest
from ....services.datastore.interface import DatastoreService
from ....shared.exceptions import ActionException, BadCodingException
from ....shared.filters import FilterOperator
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


class MergeModeDict(TypedDict, total=False):
    ignore: list[CollectionField]
    # use highest value among users
    highest: list[CollectionField]
    # raise exception if set on any user
    error: list[CollectionField]
    # use value of highest ranking user
    priority: list[CollectionField]
    # merge the lists together, filter out duplicates
    merge: list[CollectionField]
    # merge relations normally, but detect if targets serve the same function
    # and if they do, merge them together and delete the lower-rank targets
    # should only be n:1 relations
    deep_merge: list[CollectionField]
    # field has its own function
    special_function: list[CollectionField]


@register_action("user.merge_together")
class UserMergeTogether(UpdateAction, CheckForArchivedMeetingMixin):
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
        # additional_optional_fields={
        #     "password_from_user_id": {
        #         "description": "The password hash from this user is copied. The user id must be given in user_ids! If it is empty, the default password is used.",
        #         **optional_id_schema,
        #     }
        # },
    )
    permission = permission = OrganizationManagementLevel.CAN_MANAGE_USERS

    _all_collection_fields: dict[Collection, list[CollectionField]] = {
        Class.__dict__["collection"]: [
            i
            for i in Class.__dict__.keys()
            if i[:1] != "_" and i not in ["collection", "verbose_name", "id"]
        ]
        for Class in [User, MeetingUser]
    }
    _collection_field_groups: dict[Collection, MergeModeDict] = {
        "user": {
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
            "deep_merge": [
                "meeting_user_ids",
                "poll_candidate_ids",
            ],
            "special_function": [
                "organization_management_level",
                "option_ids",  # throw error if conflict on same poll, else merge
                "poll_voted_ids",  # throw error if conflict on same poll, else merge
                "vote_ids",  # throw error if conflict on same poll, else merge
                "delegated_vote_ids",  # throw error if conflict on same poll, else merge
            ],
        },
        "meeting_user": {
            "ignore": [
                "user_id",  # will be overwritten from user-side
                "meeting_id",
                "motion_editor_ids",
                "motion_working_group_speaker_ids",
            ],
            "priority": [
                "comment",
                "number",
                "about_me",
                "vote_weight",
                "vote_delegated_to_id",
            ],
            "merge": [
                "supported_motion_ids",
                "vote_delegations_from_ids",
                "chat_message_ids",
                "group_ids",
                "structure_level_ids",
            ],
            "deep_merge": [
                "motion_submitter_ids",
                "assignment_candidate_ids",
                "personal_note_ids",
            ],
            "special_function": [
                "speaker_ids",
            ],
        },
    }

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
        # TODO: Split this action into multiple user.merge_together sub-actions
        # and move the checking below into a separate merge_together base class
        # upon which they all will extend.
        for collection in self._all_collection_fields:
            broken = []
            if sorted(self._all_collection_fields[collection]) != sorted(
                field
                for group in self._collection_field_groups[collection].values()
                for field in cast(list[CollectionField], group)
                if field in self._all_collection_fields[collection]
            ):
                broken.append(collection)
            if len(broken):
                raise BadCodingException(
                    f"user.merge_together is not up-to-date for the current database definition(s) of {' and '.join(broken)}"
                )

    def prefetch(self, action_data: ActionData) -> None:
        users = self.datastore.get_many(
            [
                GetManyRequest(
                    "user",
                    [
                        id_
                        for instance in action_data
                        for id_ in set(instance.get("user_ids", []))
                    ],
                    self._all_collection_fields["user"].copy(),
                )
            ]
        )["user"]
        self.datastore.get_many(
            [
                GetManyRequest(
                    "meeting_user",
                    list(
                        {
                            id_
                            for user in users.values()
                            for id_ in user.get("meeting_user_ids", [])
                        }
                    ),
                    self._all_collection_fields["meeting_user"].copy(),
                )
            ]
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

        # TODO: Calculate data and call merge_by_rank

        raise ActionException(
            "This action is still not implemented, but permission checked"
        )
        return instance

    def merge_by_rank(
        self,
        collection: Collection,
        into: PartialModel,
        ranked_others: list[PartialModel],
        instance: dict[str, Any],
    ) -> dict[str, Any]:
        merge_modes = self._collection_field_groups[collection]
        changes: dict[str, Any] = {}
        for field in merge_modes.get("error", []):
            raise ActionException(
                "Function for error-causing fields not yet implemented"
            )
        for field in merge_modes.get("deep_merge", []):
            if (field[-4:] == "_ids") and (
                (field_collection := field[:-4]) in self._all_collection_fields
            ):
                all_field_ids: list[int] = [
                    *into.get(field, []),
                    *[id_ for model in ranked_others for id_ in model.get(field, [])],
                ]
                merge_lists: dict[Any, list[int]] = {}
                field_models = self._get_merge_by_rank_models(
                    field_collection, all_field_ids
                )
                for id_ in all_field_ids:
                    hash_val = self._get_merge_comparison_hash(
                        field_collection, field_models[id_]
                    )
                    if hash_val in merge_lists:
                        if id_ not in merge_lists[hash_val]:
                            merge_lists[hash_val].append(id_)
                    else:
                        merge_lists[hash_val] = [id_]
                new_reference_ids: list[int] = []
                for to_merge in merge_lists.values():
                    if len(to_merge) > 1:
                        to_merge_into, to_merge_others = (
                            self._split_merge_by_rank_models(
                                field_collection,
                                to_merge[0],
                                to_merge[1:],
                                field_models,
                            )
                        )
                        # TODO: Use internal sub-merge_together action instead!
                        self.merge_by_rank(
                            field_collection, to_merge_into, to_merge_others, {}
                        )
                    new_reference_ids.append(to_merge[0])
                changes[field] = new_reference_ids
        for field in merge_modes.get("special_function", []):
            match field:
                case _:
                    raise ActionException(
                        f"Function for {collection} field {field} not yet implemented"
                    )
        for field in merge_modes.get("merge", []):
            raise ActionException("Function for merge fields not yet implemented")
        for field in merge_modes.get("priority", []):
            raise ActionException(
                "Function for priority-based fields not yet implemented"
            )
        for field in merge_modes.get("highest", []):
            raise ActionException(
                "Function for highest-selection fields not yet implemented"
            )
        # TODO: self.execute_other_action(collection + ".delete", [{"id": model["id"]} for model in ranked_others])
        changes.update(
            {key: value for key, value in instance.items() if key != "user_ids"}
        )
        # TODO: Check if data is valid,
        # f.E.:shouldn't have a saml_id AND a password
        return changes

    def _get_merge_comparison_hash(
        self, collection: Collection, model: PartialModel
    ) -> int | str:
        match collection:
            case "meeting_user":
                return model["meeting_id"]
            case _:
                # TODO: Add other merge model fields
                return model["id"]  # should never merge models

    def _get_merge_by_rank_models(
        self, collection: Collection, ids: list[int]
    ) -> dict[int, PartialModel]:
        return self.datastore.get_many(
            [
                GetManyRequest(
                    collection,
                    ids,
                    self._all_collection_fields[collection].copy(),
                )
            ]
        )[collection]

    def _split_merge_by_rank_models(
        self,
        collection: Collection,
        into_id: int,
        ranked_other_ids: list[int],
        models: dict[int, PartialModel],
    ) -> tuple[PartialModel, list[PartialModel]]:
        return (
            models[into_id],
            [model for id_ in ranked_other_ids if (model := models.get(id_))],
        )

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
