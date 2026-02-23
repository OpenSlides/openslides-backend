from typing import Any, cast

from psycopg.types.json import Jsonb

from openslides_backend.services.database.interface import PartialModel

from ....action.mixins.archived_meeting_check_mixin import CheckForArchivedMeetingMixin
from ....models.models import User
from ....permissions.management_levels import OrganizationManagementLevel
from ....permissions.permission_helper import has_organization_management_level
from ....services.database.commands import GetManyRequest
from ....shared.exceptions import ActionException, BadCodingException, MissingPermission
from ....shared.filters import And, FilterOperator, Or
from ....shared.patterns import Collection, CollectionField, fqid_from_collection_and_id
from ....shared.schema import id_list_schema
from ....shared.typing import HistoryInformation
from ...generics.update import UpdateAction
from ...util.default_schema import DefaultSchema
from ...util.register import register_action
from ...util.typing import ActionData
from ..assignment_candidate.delete import AssignmentCandidateDelete
from ..assignment_candidate.update import AssignmentCandidateUpdate
from ..meeting_user.update import MeetingUserUpdate
from ..motion_editor.delete import MotionEditorDeleteAction
from ..motion_editor.update import MotionEditorUpdateAction
from ..motion_submitter.delete import MotionSubmitterDeleteAction
from ..motion_submitter.update import MotionSubmitterUpdateAction
from ..motion_supporter.delete import MotionSupporterDeleteAction
from ..motion_supporter.update import MotionSupporterUpdateAction
from ..motion_working_group_speaker.delete import MotionWorkingGroupSpeakerDeleteAction
from ..motion_working_group_speaker.update import MotionWorkingGroupSpeakerUpdateAction
from ..personal_note.create import PersonalNoteCreateAction
from ..personal_note.update import PersonalNoteUpdateAction
from ..poll.update import PollUpdateAction
from ..speaker.create_for_merge import SpeakerCreateForMerge
from ..speaker.delete import SpeakerDeleteAction
from ..speaker.update import SpeakerUpdate
from .base_merge_mixin import MergeUpdateOperations
from .delete import UserDelete
from .merge_mixins import MeetingUserMergeMixin
from .update import UserUpdate
from .user_mixins import UserMixin


@register_action("user.merge_together")
class UserMergeTogether(
    MeetingUserMergeMixin, UpdateAction, CheckForArchivedMeetingMixin
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
            "gender_id",
            "email",
            "default_vote_weight",
            "pronoun",
            "member_number",
        ],
        additional_required_fields={
            "user_ids": {
                "description": "A list of user ids to merge into a user.",
                **id_list_schema,
            },
        },
    )

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.add_collection_field_groups(
            User,
            {
                "ignore": [
                    "password",
                    "default_password",
                    "organization_id",
                    "last_email_sent",
                    "last_login",
                    "meeting_ids",
                    "committee_ids",
                    "username",
                    "is_active",
                    "is_physical_person",
                    "pronoun",
                    "title",
                    "first_name",
                    "last_name",
                    "gender_id",
                    "email",
                    "default_vote_weight",
                    "external",
                    "home_committee_id",
                ],
                "error": [
                    "is_demo_user",
                ],
                "merge": [
                    "committee_management_ids",
                    "history_entry_ids",
                    "history_position_ids",
                    "option_ids",  # throw error if conflict on same poll
                    "poll_voted_ids",  # throw error if conflict on same poll
                    "vote_ids",  # throw error if conflict on same poll
                    "delegated_vote_ids",  # throw error if conflict on same poll
                    "poll_candidate_ids",  # error if multiple of the users are on the same list, else merge
                ],
                "deep_create_merge": {
                    "meeting_user_ids": "meeting_user",
                },
                "special_function": [
                    "is_present_in_meeting_ids",  # union of primary user data and the meetings from the other users where primary is not a member
                    "organization_management_level",
                    "saml_id",  # error if set on secondary users, otherwise ignore the field
                    "member_number",
                    "can_change_own_password",  # ignore on secondary users if primary has a saml_id, else highest
                ],
            },
        )

    def check_permissions(self, instance: dict[str, Any]) -> None:
        selected_users = self.datastore.get_many(
            [
                GetManyRequest(
                    "user",
                    [instance["id"], *instance["user_ids"]],
                    ["organization_management_level"],
                )
            ]
        )["user"]
        all_omls = [
            OrganizationManagementLevel(oml)
            for user in selected_users.values()
            if (oml := user.get("organization_management_level"))
        ]
        min_oml = max([*all_omls, OrganizationManagementLevel.CAN_MANAGE_USERS])
        if not has_organization_management_level(
            self.datastore,
            self.user_id,
            min_oml,
        ):
            raise MissingPermission(min_oml)

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
            id_
            for instance in action_data
            for id_ in {*instance.get("user_ids", []), instance["id"]}
        ]
        if len(user_ids) != len(set(user_ids)):
            raise ActionException(
                "Users cannot be part of different merges at the same time"
            )
        secondary_id_to_main_ids = {
            user_id: instance["id"]
            for instance in action_data
            for user_id in instance.get("user_ids", [])
        }
        polls = self.datastore.filter(
            "poll",
            And(
                FilterOperator("entitled_users_at_stop", "!=", None),
                FilterOperator("entitled_users_at_stop", "!=", Jsonb([])),
            ),
            ["entitled_users_at_stop"],
        )
        poll_payloads: list[dict[str, Any]] = []
        for id_, poll in polls.items():
            entitled: list[dict[str, Any]] = poll["entitled_users_at_stop"]
            changed = False
            for vote in entitled:
                if (
                    user_id := (vote.get("user_merged_into_id") or vote.get("user_id"))
                ) in secondary_id_to_main_ids:
                    vote["user_merged_into_id"] = secondary_id_to_main_ids[user_id]
                    changed = True
                if (
                    user_id := (
                        vote.get("delegation_user_merged_into_id")
                        or vote.get("vote_delegated_to_user_id")
                    )
                ) in secondary_id_to_main_ids:
                    vote["delegation_user_merged_into_id"] = secondary_id_to_main_ids[
                        user_id
                    ]
                    changed = True
            if changed:
                poll_payloads.append({"id": id_, "entitled_users_at_stop": entitled})
        if len(poll_payloads):
            self.execute_other_action(PollUpdateAction, poll_payloads)
        return super().get_updated_instances(action_data)

    def update_instance(self, instance: dict[str, Any]) -> dict[str, Any]:
        instance = super().update_instance(instance)
        update_operations: dict[Collection, MergeUpdateOperations] = {
            coll: {"create": [], "update": [], "delete": []}
            for coll in self._collection_field_groups
        }
        if self.user_id in instance["user_ids"]:
            raise ActionException("Operator may not merge himself into others.")

        models = self.get_merge_by_rank_models(
            "user", [instance["id"], *instance["user_ids"]]
        )
        into, other_models = self.split_merge_by_rank_models(
            instance["id"], instance["user_ids"], models
        )

        self.check_polls(into, other_models)
        self.check_speakers(
            list(
                {
                    meeting_user_id
                    for model in [into, *other_models]
                    for meeting_user_id in model.get("meeting_user_ids", [])
                }
            )
        )

        update_operations["user"]["update"].append(
            self.merge_by_rank("user", into, other_models, instance, update_operations)
        )

        self.call_other_actions(update_operations)

        result = {"id": into["id"]}
        self._history_replacement_groups["user"].append(
            (result, [into["id"], *instance["user_ids"]], False)
        )
        return result

    def call_other_actions(
        self, update_operations: dict[Collection, MergeUpdateOperations]
    ) -> None:
        if len(update_operations["user"]["update"]) != 1:
            raise BadCodingException("Calculated wrong amount of user payloads")
        main_user_payload = update_operations["user"]["update"][0]
        main_user_id = main_user_payload["id"]
        meeting_user_create_payloads = update_operations["meeting_user"]["create"]
        if len(
            update_payloads := [
                *update_operations["meeting_user"]["update"],
                *meeting_user_create_payloads,
            ]
        ):
            meeting_user_via_user_payloads = []
            for payload_index in range(len(update_payloads)):
                current = update_payloads[payload_index]
                meeting_user_via_user_payloads.append(
                    {
                        "id": main_user_id,
                        "meeting_id": current["meeting_id"],
                        **{
                            field: current.pop(field)
                            for field in UserMixin.transfer_field_list
                            if field in current
                        },
                    }
                )
            self.execute_other_action(UserUpdate, meeting_user_via_user_payloads)

            meeting_user_update_payloads = [
                payload
                for payload in update_operations["meeting_user"]["update"]
                if len(payload) > 1
            ]
            new_meeting_ids = [
                m_user["meeting_id"] for m_user in meeting_user_create_payloads
            ]
            if len(new_meeting_ids):
                new_meeting_users = self.datastore.filter(
                    "meeting_user",
                    And(
                        FilterOperator("user_id", "=", main_user_id),
                        Or(
                            FilterOperator("meeting_id", "=", meeting_id)
                            for meeting_id in new_meeting_ids
                        ),
                    ),
                    ["meeting_id"],
                )
            else:
                new_meeting_users = {}
            meeting_user_ids_by_meeting_ids = {
                m_user["meeting_id"]: id_ for id_, m_user in new_meeting_users.items()
            }
            for payload in meeting_user_create_payloads:
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

            update_operations["personal_note"]["create"] = [
                payload
                for payload in update_operations["personal_note"]["create"]
                if payload.get("star") or payload.get("note")
            ]

            meeting_user_id_by_meeting_id = {
                model["meeting_id"]: id_
                for id_, model in self.datastore.filter(
                    "meeting_user",
                    FilterOperator("user_id", "=", main_user_id),
                    ["meeting_id"],
                ).items()
            }

            create_deep_merge_actions_per_collection: dict[str, dict[str, Any]] = {
                "personal_note": {
                    "update": PersonalNoteUpdateAction,
                    "create": PersonalNoteCreateAction,
                },
                "speaker": {
                    "update": SpeakerUpdate,
                    "create": SpeakerCreateForMerge,
                    "delete": SpeakerDeleteAction,
                },
                "assignment_candidate": {
                    "update": AssignmentCandidateUpdate,
                    "delete": AssignmentCandidateDelete,
                },
                "motion_supporter": {
                    "update": MotionSupporterUpdateAction,
                    "delete": MotionSupporterDeleteAction,
                },
                "motion_submitter": {
                    "update": MotionSubmitterUpdateAction,
                    "delete": MotionSubmitterDeleteAction,
                },
                "motion_editor": {
                    "update": MotionEditorUpdateAction,
                    "delete": MotionEditorDeleteAction,
                },
                "motion_working_group_speaker": {
                    "update": MotionWorkingGroupSpeakerUpdateAction,
                    "delete": MotionWorkingGroupSpeakerDeleteAction,
                },
            }

            for collection, actions in create_deep_merge_actions_per_collection.items():
                if "create" in actions and len(
                    to_create := update_operations[collection]["create"]
                ):
                    for payload in to_create:
                        meeting_id = payload.pop("meeting_id")
                        payload["meeting_user_id"] = meeting_user_id_by_meeting_id[
                            meeting_id
                        ]
                    self.execute_other_action(
                        actions["create"],
                        to_create,
                    )
                if "update" in actions and len(
                    to_update := [
                        payload
                        for payload in update_operations[collection]["update"]
                        if len(payload) > 1
                    ]
                ):
                    self.execute_other_action(
                        actions["update"],
                        to_update,
                    )
                if "delete" in actions and len(
                    to_delete := update_operations[collection]["delete"]
                ):
                    self.execute_other_action(
                        actions["delete"],
                        [{"id": id_} for id_ in to_delete],
                    )

        self.execute_other_action(UserUpdate, [main_user_payload])
        if len(to_delete := update_operations["user"]["delete"]):
            self.execute_other_action(
                UserDelete,
                [{"id": id_} for id_ in to_delete],
            )

    def check_polls(self, into: PartialModel, other_models: list[PartialModel]) -> None:
        all_models = [into, *other_models]
        vote_poll_ids_per_user_id: dict[int, set[int]] = {
            user["id"]: {poll_id for poll_id in user.get("poll_voted_ids", [])}
            for user in [into, *other_models]
        }
        option_poll_ids_per_user_id: dict[int, set[int]] = {}
        candidate_list_ids_per_user_id: dict[int, set[int]] = {}
        meeting_user_ids: list[int] = []
        for model in all_models:
            if len(
                (pc_ids := model.get("poll_candidate_ids", []))
                + (o_ids := model.get("option_ids", []))
                + (
                    v_ids := list(
                        {
                            id_
                            for id_ in [
                                *model.get("vote_ids", []),
                                *model.get("delegated_vote_ids", []),
                            ]
                        }
                    )
                )
            ):
                get_many_requests = [
                    GetManyRequest(
                        "poll_candidate", pc_ids, ["poll_candidate_list_id"]
                    ),
                    GetManyRequest(
                        "option",
                        o_ids,
                        ["poll_id"],
                    ),
                    GetManyRequest(
                        "vote",
                        v_ids,
                        ["option_id"],
                    ),
                ]
                many_models = self.datastore.get_many(get_many_requests)
                if pc_ids:
                    candidate_list_ids_per_user_id[model["id"]] = {
                        poll_candidate["poll_candidate_list_id"]
                        for poll_candidate in many_models["poll_candidate"].values()
                        if poll_candidate.get("poll_candidate_list_id")
                    }
                if o_ids:
                    option_poll_ids_per_user_id[model["id"]] = {
                        option["poll_id"]
                        for option in many_models["option"].values()
                        if option.get("poll_id")
                    }
                vote_data = many_models["vote"]
                vote_poll_ids_per_user_id[model["id"]] = {
                    *vote_poll_ids_per_user_id.get(model["id"], set()),
                    *{
                        cast(int, option["poll_id"])
                        for option in self.datastore.get_many(
                            [
                                GetManyRequest(
                                    "option",
                                    list(
                                        {
                                            id_
                                            for id_ in [
                                                vote["option_id"]
                                                for vote in vote_data.values()
                                                if vote.get("option_id")
                                            ]
                                        }
                                    ),
                                    ["poll_id"],
                                )
                            ]
                        )["option"].values()
                        if option.get("poll_id")
                    },
                }
            meeting_user_ids += model.get("meeting_user_ids", [])
        voting_conflicts = {
            poll_id
            for id1, poll_ids1 in vote_poll_ids_per_user_id.items()
            for id2, poll_ids2 in vote_poll_ids_per_user_id.items()
            for poll_id in poll_ids1.intersection(poll_ids2)
            if id1 != id2
        }
        option_conflicts = {
            poll_id
            for id1, poll_ids1 in option_poll_ids_per_user_id.items()
            for id2, poll_ids2 in option_poll_ids_per_user_id.items()
            for poll_id in poll_ids1.intersection(poll_ids2)
            if id1 != id2
        }
        candidate_list_conflicts = {
            list_id
            for id1, list_ids1 in candidate_list_ids_per_user_id.items()
            for id2, list_ids2 in candidate_list_ids_per_user_id.items()
            for list_id in list_ids1.intersection(list_ids2)
            if id1 != id2
        }
        messages: list[str] = self.check_polls_helper(meeting_user_ids)
        if len(voting_conflicts):
            messages.append(
                f"among the selected users multiple voted in poll(s) {', '.join([str(id_) for id_ in voting_conflicts])}"
            )
        if len(option_conflicts):
            messages.append(
                f"multiple of the selected users are among the options in poll(s) {', '.join([str(id_) for id_ in option_conflicts])}"
            )
        if len(candidate_list_conflicts):
            lists = self.datastore.get_many(
                [
                    GetManyRequest(
                        "poll_candidate_list",
                        list(candidate_list_conflicts),
                        ["option_id"],
                    )
                ],
                lock_result=False,
            )["poll_candidate_list"]
            option_ids = {c_list["option_id"] for c_list in lists.values()}
            options = self.datastore.get_many(
                [GetManyRequest("option", list(option_ids), ["poll_id"])],
                lock_result=False,
            )["option"]
            poll_ids = {option["poll_id"] for option in options.values()}
            messages.append(
                f"multiple of the selected users are in the same candidate list in poll(s) {', '.join([str(id_) for id_ in poll_ids])}"
            )
        if len(messages):
            raise ActionException(
                f"Cannot carry out merge into user/{into['id']}, because {' and '.join(messages)}"
            )

    def get_merge_comparison_hash(
        self, collection: Collection, model: PartialModel
    ) -> int | str | tuple[int | str, ...]:
        match collection:
            case "meeting_user":
                return model["meeting_id"]
            case _:
                return super().get_merge_comparison_hash(collection, model)

    def handle_special_field(
        self,
        collection: Collection,
        field: CollectionField,
        into_: PartialModel,
        ranked_others: list[PartialModel],
        update_operations: dict[Collection, MergeUpdateOperations],
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
                case "is_present_in_meeting_ids":
                    all_meeting_ids = self.get_meeting_ids_per_user(
                        [into_, *ranked_others]
                    )
                    check_meeting_ids = all_meeting_ids[into_["id"]]
                    present_meeting_ids: set[int] = set(into_.get(field, []))
                    for other in ranked_others:
                        present_meeting_ids.update(
                            set(other.get(field, [])).difference(check_meeting_ids)
                        )
                        check_meeting_ids.update(all_meeting_ids[other["id"]])
                    return list(present_meeting_ids)
                case "member_number":
                    self.check_equality(
                        collection, into_, ranked_others, into_["id"], field
                    )
                    return None
                case "can_change_own_password":
                    if into_.get("saml_id"):
                        return None
                    if len(
                        comp_data := [
                            date
                            for model in [into_, *ranked_others]
                            if (date := model.get("can_change_own_password"))
                            is not None
                        ]
                    ):
                        return any(comp_data)
                    return None
        return super().handle_special_field(
            collection, field, into_, ranked_others, update_operations
        )

    def get_meeting_ids_per_user(
        self, users: list[PartialModel]
    ) -> dict[int, set[int]]:
        meeting_users = self.datastore.filter(
            "meeting_user",
            And(
                FilterOperator("group_ids", "!=", []),
                Or(FilterOperator("user_id", "=", user["id"]) for user in users),
            ),
            ["meeting_id"],
        )
        return {
            user["id"]: {
                meeting_id
                for meeting_user_id in user.get("meeting_user_ids", [])
                if (
                    meeting_id := meeting_users.get(meeting_user_id, {}).get(
                        "meeting_id"
                    )
                )
            }
            for user in users
        }

    def get_full_history_information(self) -> HistoryInformation | None:
        information = super().get_full_history_information() or {}
        for data, ids, is_transfer in self._history_replacement_groups["user"]:
            main_id = data.get("id")
            if main_id:
                main_fqid = fqid_from_collection_and_id("user", main_id)
                deleted_fqids = [
                    fqid_from_collection_and_id("user", id_)
                    for id_ in ids
                    if id_ != main_id
                ]
                if len(deleted_fqids) > 2:
                    deleted_string = (
                        ", ".join(["{}" for i in range(len(deleted_fqids) - 1)])
                        + " and {}"
                    )
                else:
                    deleted_string = " and ".join(
                        ["{}" for i in range(len(deleted_fqids))]
                    )
                information[main_fqid] = [
                    "Updated with data from " + deleted_string,
                    *deleted_fqids,
                ]
                for deleted_fqid in deleted_fqids:
                    information[deleted_fqid] = ["Merged into {}", main_fqid]
            else:
                raise BadCodingException("No id found for user history generation")
        return information
