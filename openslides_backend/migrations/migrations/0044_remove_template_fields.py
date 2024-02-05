from collections import defaultdict
from collections.abc import Callable
from enum import Enum, auto
from typing import Any, NamedTuple, TypedDict

from datastore.migrations import BaseModelMigration, MigrationException
from datastore.writer.core import (
    BaseRequestEvent,
    RequestCreateEvent,
    RequestUpdateEvent,
)

from openslides_backend.shared.patterns import (
    Collection,
    FullQualifiedId,
    fqid_from_collection_and_id,
)


class FieldStrategy(Enum):
    """
    Defines various strategies for handling template/structured fields.
    Reminder: structured fields are template fields with inserted replacement.
    """

    Rename = auto()
    """
    Rename all structured fields and remove this template field.
    """

    Merge = auto()
    """
    Merges all replacements of this template field into one field.
    """

    MergeToJSON = auto()
    """
    Builds a JSON object from all structured fields of this template field.
    """

    MoveToMeetingUser = auto()
    """
    Moves this `user` template field to the `meeting_user` collection.
    """

    ReplaceWithMeetingUsers = auto()
    """
    Replaces this relation field pointing to the `user` collection with a list of `meeting_user` ids.
    """

    MoveToMeetingUserAndReplace = auto()
    """
    Combination of MoveToMeetingUser and ReplaceWithMeetingUsers. Used for previous self-referencing
    `user` fields which are now fields of `meeting_user`.
    """


FieldNameFunc = Callable[[str], str]


class ParametrizedFieldStrategy(TypedDict):
    strategy: FieldStrategy
    name: str | dict[str, str]


TEMPLATE_FIELDS: dict[
    Collection, dict[str, FieldStrategy | ParametrizedFieldStrategy]
] = {
    "user": {
        "committee_$_management_level": {
            "strategy": FieldStrategy.Rename,
            "name": "committee_management_ids",
        },
        "poll_voted_$_ids": FieldStrategy.Merge,
        "option_$_ids": FieldStrategy.Merge,
        "vote_$_ids": FieldStrategy.Merge,
        "vote_delegated_vote_$_ids": {
            "strategy": FieldStrategy.Merge,
            "name": "delegated_vote_ids",
        },
        "comment_$": FieldStrategy.MoveToMeetingUser,
        "number_$": FieldStrategy.MoveToMeetingUser,
        "structure_level_$": FieldStrategy.MoveToMeetingUser,
        "about_me_$": FieldStrategy.MoveToMeetingUser,
        "vote_weight_$": FieldStrategy.MoveToMeetingUser,
        "group_$_ids": FieldStrategy.MoveToMeetingUser,
        "speaker_$_ids": FieldStrategy.MoveToMeetingUser,
        "personal_note_$_ids": FieldStrategy.MoveToMeetingUser,
        "supported_motion_$_ids": FieldStrategy.MoveToMeetingUser,
        "submitted_motion_$_ids": {
            "strategy": FieldStrategy.MoveToMeetingUser,
            "name": "motion_submitter_ids",
        },
        "assignment_candidate_$_ids": FieldStrategy.MoveToMeetingUser,
        "vote_delegated_$_to_id": FieldStrategy.MoveToMeetingUserAndReplace,
        "vote_delegations_$_from_ids": FieldStrategy.MoveToMeetingUserAndReplace,
        "chat_message_$_ids": FieldStrategy.MoveToMeetingUser,
    },
    "committee": {
        "user_$_management_level": {
            "strategy": FieldStrategy.Rename,
            "name": "manager_ids",
        },
    },
    "meeting": {
        "logo_$_id": FieldStrategy.Rename,
        "font_$_id": FieldStrategy.Rename,
        "default_projector_$_ids": {
            "strategy": FieldStrategy.Rename,
            "name": {
                "default_projector_$agenda_all_items_ids": "default_projector_agenda_item_list_ids",
                "default_projector_$topics_ids": "default_projector_topic_ids",
                "default_projector_$projector_countdowns_ids": "default_projector_countdown_ids",
                "default_projector_$projector_message_ids": "default_projector_message_ids",
            },
        },
    },
    "group": {
        "user_ids": FieldStrategy.ReplaceWithMeetingUsers,
    },
    "motion": {
        "amendment_paragraphs_$": {
            "strategy": FieldStrategy.MergeToJSON,
            "name": "amendment_paragraphs",
        },
        "supporter_ids": {
            "strategy": FieldStrategy.ReplaceWithMeetingUsers,
            "name": "supporter_meeting_user_ids",
        },
    },
    "mediafile": {
        "used_as_logo_$_in_meeting_id": FieldStrategy.Rename,
        "used_as_font_$_in_meeting_id": FieldStrategy.Rename,
    },
    "projector": {
        "used_as_default_$_in_meeting_id": {
            "strategy": FieldStrategy.Rename,
            "name": {
                "used_as_default_$agenda_all_items_in_meeting_id": "used_as_default_projector_for_agenda_item_list_in_meeting_id",
                "used_as_default_$topics_in_meeting_id": "used_as_default_projector_for_topic_in_meeting_id",
                "used_as_default_$list_of_speakers_in_meeting_id": "used_as_default_projector_for_list_of_speakers_in_meeting_id",
                "used_as_default_$current_list_of_speakers_in_meeting_id": "used_as_default_projector_for_current_list_of_speakers_in_meeting_id",
                "used_as_default_$motion_in_meeting_id": "used_as_default_projector_for_motion_in_meeting_id",
                "used_as_default_$amendment_in_meeting_id": "used_as_default_projector_for_amendment_in_meeting_id",
                "used_as_default_$motion_block_in_meeting_id": "used_as_default_projector_for_motion_block_in_meeting_id",
                "used_as_default_$assignment_in_meeting_id": "used_as_default_projector_for_assignment_in_meeting_id",
                "used_as_default_$mediafile_in_meeting_id": "used_as_default_projector_for_mediafile_in_meeting_id",
                "used_as_default_$projector_message_in_meeting_id": "used_as_default_projector_for_message_in_meeting_id",
                "used_as_default_$projector_countdowns_in_meeting_id": "used_as_default_projector_for_countdown_in_meeting_id",
                "used_as_default_$assignment_poll_in_meeting_id": "used_as_default_projector_for_assignment_poll_in_meeting_id",
                "used_as_default_$motion_poll_in_meeting_id": "used_as_default_projector_for_motion_poll_in_meeting_id",
                "used_as_default_$poll_in_meeting_id": "used_as_default_projector_for_poll_in_meeting_id",
            },
        }
    },
    "personal_note": {
        "user_id": FieldStrategy.ReplaceWithMeetingUsers,
    },
    "speaker": {
        "user_id": FieldStrategy.ReplaceWithMeetingUsers,
    },
    "motion_submitter": {
        "user_id": FieldStrategy.ReplaceWithMeetingUsers,
    },
    "assignment_candidate": {
        "user_id": FieldStrategy.ReplaceWithMeetingUsers,
    },
    "chat_message": {
        "user_id": FieldStrategy.ReplaceWithMeetingUsers,
    },
}


class MeetingUserKey(NamedTuple):
    meeting_id: int
    user_id: int


class MeetingUsersDict(dict[MeetingUserKey, dict[str, Any]]):
    last_id: int
    ids_by_parent_object: dict[Collection, dict[int, list[int]]]

    def __init__(self, *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.last_id = 0
        self.ids_by_parent_object = {
            "user": defaultdict(list),
            "meeting": defaultdict(list),
        }

    def __missing__(self, key: MeetingUserKey) -> dict[str, Any]:
        self.last_id += 1
        self.ids_by_parent_object["user"][key.user_id].append(self.last_id)
        self.ids_by_parent_object["meeting"][key.meeting_id].append(self.last_id)
        self[key] = {
            "id": self.last_id,
            "user_id": key.user_id,
            "meeting_id": key.meeting_id,
        }
        return self[key]


class Migration(BaseModelMigration):
    """
    This migration removes all template fields. It iterates over the fields in TEMPLATE_FIELDS,
    where a _strategy_ is defined for each field, potentially with a differing new name for the
    field. The strategy defines how the field is migrated. It is first _resolved_ into the actual
    strategy enum and a function that converts the old field name into the new one. Then, the
    strategy is _applied_ to all models in the database which results in a list of updates to the
    models. Lastly, the events are generated from these updates and the meeting users which were
    created along the way.
    """

    target_migration_index = 45

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        self.meeting_users = MeetingUsersDict()
        updates: dict[FullQualifiedId, dict[str, Any]] = defaultdict(dict)

        for collection, fields in TEMPLATE_FIELDS.items():
            db_models = self.reader.get_all(collection)
            for id, model in db_models.items():
                update = updates[fqid_from_collection_and_id(collection, id)]
                for old_field, _strategy in fields.items():
                    if old_field in model:
                        strategy, new_field_func = self.resolve_strategy(_strategy)
                        # all user template fields except committee_$_management_level have the
                        # meeting as replacement collection
                        replacement_collection = (
                            "meeting"
                            if collection == "user"
                            and old_field != "committee_$_management_level"
                            else None
                        )
                        update.update(
                            **self.apply_strategy(
                                model,
                                strategy,
                                old_field,
                                new_field_func,
                                replacement_collection,
                            )
                        )

        events: list[BaseRequestEvent] = []
        # Create meeting users
        events.extend(
            RequestCreateEvent(
                fqid_from_collection_and_id("meeting_user", model["id"]), model
            )
            for model in self.meeting_users.values()
        )
        # Update meetings and users with meeting users
        for collection in ("meeting", "user"):
            events.extend(
                RequestUpdateEvent(
                    fqid_from_collection_and_id(collection, parent_id),
                    {"meeting_user_ids": meeting_user_ids},
                )
                for parent_id, meeting_user_ids in self.meeting_users.ids_by_parent_object[
                    collection
                ].items()
            )
        # Create all other update events
        events.extend(
            RequestUpdateEvent(fqid, model) for fqid, model in updates.items() if model
        )
        return events

    def apply_strategy(
        self,
        model: dict[str, Any],
        strategy: FieldStrategy,
        old_field: str,
        new_field_func: FieldNameFunc,
        replacement_collection: str | None,
    ) -> dict[str, Any]:
        # always remove the old field
        update: dict[str, Any] = {
            old_field: None,
        }

        def get_meeting_user_ids(
            meeting_id: int, user_ids: int | list[int]
        ) -> int | list[int]:
            if isinstance(user_ids, list):
                return [
                    self.meeting_users[MeetingUserKey(meeting_id, user_id)]["id"]
                    for user_id in user_ids
                ]
            else:
                key = MeetingUserKey(meeting_id, user_ids)
                return self.meeting_users[key]["id"]

        new_field = new_field_func(old_field)
        if strategy is FieldStrategy.ReplaceWithMeetingUsers:
            # replace user ids with meeting_user ids
            update[new_field] = get_meeting_user_ids(
                model["meeting_id"], model[old_field]
            )
        else:
            new_value: list[Any] = []
            for replacement in model[old_field]:
                structured_field = old_field.replace("$", f"${replacement}")
                # always remove the old field
                update[structured_field] = None

                if replacement_collection:
                    # check if the replacement actually exists, otherwise skip it
                    fqid = fqid_from_collection_and_id(
                        replacement_collection, replacement
                    )
                    if not self.reader.is_alive(fqid):
                        continue

                if structured_value := model.get(structured_field):
                    if strategy is FieldStrategy.Rename:
                        # move value to new field
                        new_structured_field = new_field_func(structured_field)
                        update[new_structured_field] = structured_value
                    elif strategy is FieldStrategy.Merge:
                        # merge values together into a single list
                        new_value.extend(structured_value)
                    elif strategy is FieldStrategy.MergeToJSON:
                        # merge values together into a single list of key-value pairs
                        new_value.append((replacement, structured_value))
                    elif strategy in (
                        FieldStrategy.MoveToMeetingUser,
                        FieldStrategy.MoveToMeetingUserAndReplace,
                    ):
                        # move value to new field in meeting_user
                        meeting_id = int(replacement)
                        key = MeetingUserKey(meeting_id, model["id"])
                        # replace user ids with meeting_user ids, if necessary
                        self.meeting_users[key][new_field] = (
                            structured_value
                            if strategy is FieldStrategy.MoveToMeetingUser
                            else get_meeting_user_ids(meeting_id, structured_value)
                        )
                    else:
                        raise MigrationException("Invalid strategy")

            if new_value:
                if strategy is FieldStrategy.MergeToJSON:
                    # make dict from key-value pairs
                    update[new_field] = dict(new_value)
                else:
                    update[new_field] = new_value
        return update

    def resolve_strategy(
        self, strategy: FieldStrategy | ParametrizedFieldStrategy
    ) -> tuple[FieldStrategy, FieldNameFunc]:
        """
        Resolves a (parametrized) strategy to a tuple of strategy and the new field name.
        """
        if isinstance(strategy, dict):
            return (strategy["strategy"], self.get_name_func_from_parameters(strategy))
        else:
            return (strategy, self.get_name_func_for_strategy(strategy))

    def get_name_func_from_parameters(
        self, strategy: ParametrizedFieldStrategy
    ) -> FieldNameFunc:
        # see https://github.com/python/mypy/issues/4297 for an explanation for the redundant variables
        if isinstance(strategy["name"], str):
            name = strategy["name"]
            return lambda _: name
        elif isinstance(strategy["name"], dict):
            name_map = strategy["name"]
            return lambda field: (
                name_map[field] if field in name_map else field.replace("$", "")
            )
        else:
            raise MigrationException("Invalid name parameter")

    def get_name_func_for_strategy(self, strategy: FieldStrategy) -> FieldNameFunc:
        if strategy is FieldStrategy.Rename:
            return lambda field: field.replace("$", "")
        elif strategy in (
            FieldStrategy.Merge,
            FieldStrategy.MergeToJSON,
            FieldStrategy.MoveToMeetingUser,
            FieldStrategy.MoveToMeetingUserAndReplace,
        ):
            return lambda field: field.replace("_$", "")
        elif strategy is FieldStrategy.ReplaceWithMeetingUsers:
            return lambda field: f"meeting_{field}"
        else:
            raise MigrationException("Invalid strategy")
