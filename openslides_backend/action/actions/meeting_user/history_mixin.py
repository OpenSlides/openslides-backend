from collections.abc import Iterable
from copy import deepcopy
from typing import Any

from openslides_backend.action.mixins.extend_history_mixin import ExtendHistoryMixin
from openslides_backend.shared.interfaces.event import Event, EventType

from ....services.datastore.interface import GetManyRequest
from ....shared.patterns import fqid_from_collection_and_id
from ....shared.typing import HistoryInformation
from ...action import Action


class MeetingUserHistoryMixin(ExtendHistoryMixin, Action):
    extend_history_to = "user_id"

    def create_events(self, instance: dict[str, Any]) -> Iterable[Event]:
        yield from super().create_events(instance)
        db_instance = self.datastore.get(
            fqid_from_collection_and_id("meeting_user", instance["id"]),
            ["vote_delegated_to_id", "vote_delegations_from_ids"],
            use_changed_models=False,
            raise_exception=False,
            lock_result=False,
        )
        meeting_user_ids = set(instance.get("vote_delegations_from_ids", []))
        if "vote_delegations_from_ids" in instance:
            added_delegations = list(
                meeting_user_ids.difference(
                    db_instance.get("vote_delegations_from_ids", [])
                )
            )
            meeting_user_ids.update(db_instance.get("vote_delegations_from_ids", []))
            if added_delegations:
                db_added_to_ids = [
                    date["vote_delegated_to_id"]
                    for date in self.datastore.get_many(
                        [
                            GetManyRequest(
                                "meeting_user",
                                added_delegations,
                                ["vote_delegated_to_id"],
                            )
                        ],
                        use_changed_models=False,
                        lock_result=False,
                    )["meeting_user"].values()
                    if date.get("vote_delegated_to_id")
                ]
                meeting_user_ids.update(db_added_to_ids)
        if muser_id := instance.get("vote_delegated_to_id"):
            meeting_user_ids.add(muser_id)
        if "vote_delegated_to_id" in instance and db_instance.get(
            "vote_delegated_to_id"
        ):
            meeting_user_ids.add(db_instance["vote_delegated_to_id"])
        if meeting_user_ids:
            user_ids: set[int] = {
                muser["user_id"]
                for muser in self.datastore.get_many(
                    [
                        GetManyRequest(
                            "meeting_user", list(meeting_user_ids), ["user_id"]
                        )
                    ],
                    lock_result=False,
                )
                .get("meeting_user", {})
                .values()
            }
            for user_id in user_ids:
                yield self.build_event(
                    EventType.Update,
                    fqid_from_collection_and_id("user", user_id),
                    {"id": user_id},
                )

    def get_history_information(self) -> HistoryInformation | None:
        information: dict[str, list[tuple[str, ...]]] = {}

        # Scan the instances and collect the info for the history information
        # Copy instances first since they are modified
        for instance in deepcopy(self.instances):
            # Fetch the current instance from the db to diff with the given instance
            db_instance = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                list(instance.keys()) + ["user_id", "meeting_id"],
                use_changed_models=False,
                raise_exception=False,
                lock_result=False,
            )
            if not db_instance:
                self.add_created_meeting_user_history_information(instance, information)
            else:
                self.add_updated_meeting_user_history_information(
                    instance, db_instance, information
                )

        return {
            fqid: [string for entry in history for string in entry]
            for fqid, history in information.items()
        }

    def add_updated_meeting_user_history_information(
        self,
        instance: dict[str, Any],
        db_instance: dict[str, Any],
        information: dict[str, list[tuple[str, ...]]],
    ) -> None:
        instance_information: list[tuple[str, ...]] = []
        user_id = db_instance["user_id"]
        meeting_id = db_instance["meeting_id"]

        # Compare db version with payload
        for field in list(instance.keys()):
            # Remove fields if equal
            if instance[field] == db_instance.get(field):
                del instance[field]

        # meeting specific data
        update_fields = ["structure_level_ids", "number", "vote_weight"]
        if any(field in instance for field in update_fields):
            instance_information.append(
                (
                    "Participant data updated in meeting {}",
                    fqid_from_collection_and_id("meeting", meeting_id),
                )
            )

        self.handle_group_updates(instance_information, instance, db_instance)
        self.handle_delegations(
            information, instance_information, instance, db_instance
        )

        if instance_information:
            self.add_entries_to_history_information(
                information, instance_information, for_user_id=user_id
            )

    def add_created_meeting_user_history_information(
        self, instance: dict[str, Any], information: dict[str, list[tuple[str, ...]]]
    ) -> None:
        db_instance = self.datastore.get(
            fqid_from_collection_and_id(self.model.collection, instance["id"]),
            ["user_id", "meeting_id"],
            lock_result=False,
        )
        instance_information: list[tuple[str, ...]] = []
        fqids_per_collection = {
            collection_name: [
                fqid_from_collection_and_id(
                    collection_name,
                    _id,
                )
                for _id in ids
            ]
            for collection_name in ["group", "structure_level"]
            if (ids := instance.get(f"{collection_name}_ids"))
        }
        history_string_fqids = [
            fqid for fqids in fqids_per_collection.values() for fqid in fqids
        ]
        if history_string_fqids:
            instance_information.append(
                (
                    self.compose_history_string(list(fqids_per_collection.items())),
                    *history_string_fqids,
                    fqid_from_collection_and_id("meeting", db_instance["meeting_id"]),
                )
            )

        self.handle_delegations(
            information, instance_information, instance, db_instance
        )

        if instance_information:
            self.add_entries_to_history_information(
                information, instance_information, for_user_id=db_instance["user_id"]
            )

    def add_entries_to_history_information(
        self,
        information: dict[str, list[tuple[str, ...]]],
        entries: list[tuple[str, ...]],
        for_user_id: int | None = None,
        for_meeting_user_id: int | None = None,
    ) -> None:
        if not for_user_id:
            if not for_meeting_user_id:
                raise Exception("Can't add history entry without a target user id.")
            user_id = self.datastore.get(
                fqid_from_collection_and_id("meeting_user", for_meeting_user_id),
                ["user_id"],
                lock_result=False,
            )["user_id"]
        else:
            user_id = for_user_id
        fqid = fqid_from_collection_and_id("user", user_id)
        if fqid not in information:
            information[fqid] = entries
        else:
            for entry in entries:
                if entry not in information[fqid]:
                    information[fqid].append(entry)

    def compose_history_string(
        self, fqids_per_collection: list[tuple[str, list[str]]]
    ) -> str:
        """
        Composes a string of the shape:
        Participant added to groups {}, {} and structure levels {} in meeting {}.
        """
        middle_sentence_parts = [
            " ".join(
                [  # prefix and to collection name if it's not the first in list
                    ("and " if collection_name != fqids_per_collection[0][0] else "")
                    + collection_name.replace("_", " ")  # replace for human readablity
                    + ("s" if len(fqids) != 1 else ""),  # plural s
                    ", ".join(["{}" for _ in range(len(fqids))]),
                ]
            )
            for collection_name, fqids in fqids_per_collection
        ]
        return " ".join(
            [
                "Participant added to",
                *middle_sentence_parts,
                ("in " if fqids_per_collection else "") + "meeting {}.",
            ]
        )

    def handle_group_updates(
        self,
        instance_information: list[tuple[str, ...]],
        instance: dict[str, Any],
        db_instance: dict[str, Any],
    ) -> None:
        if "group_ids" in instance:
            meeting_id = db_instance["meeting_id"]
            instance_group_ids = set(instance["group_ids"])
            db_group_ids = set(db_instance.get("group_ids", []))
            added = instance_group_ids - db_group_ids
            removed = db_group_ids - instance_group_ids

            # remove default groups
            meeting = self.datastore.get(
                fqid_from_collection_and_id("meeting", meeting_id),
                ["default_group_id"],
                lock_result=False,
            )
            added.discard(meeting.get("default_group_id"))
            removed.discard(meeting.get("default_group_id"))
            changed = added | removed

            group_information: list[str] = []
            if added and removed:
                group_information.append("Groups changed")
            else:
                if added:
                    group_information.append("Participant added to")
                else:
                    group_information.append("Participant removed from")
                if len(changed) == 1:
                    group_information[0] += " group {} in"
                    changed_group = changed.pop()
                    group_information.append(
                        fqid_from_collection_and_id("group", changed_group)
                    )
                elif instance_group_ids:
                    group_information[0] += " multiple groups in"
                group_information[0] += " meeting {}"
                group_information.append(
                    fqid_from_collection_and_id("meeting", meeting_id)
                )
            instance_information.append(tuple(group_information))

    def handle_delegations(
        self,
        information: dict[str, list[tuple[str, ...]]],
        instance_information: list[tuple[str, ...]],
        instance: dict[str, Any],
        db_instance: dict[str, Any],
    ) -> None:
        meeting_id = db_instance["meeting_id"]
        user_id = db_instance["user_id"]
        if "vote_delegated_to_id" in instance:
            if (
                (old_to_muser_id := db_instance.get("vote_delegated_to_id"))
                and old_to_muser_id != instance["vote_delegated_to_id"]
                and (
                    old_to_user_id := self.datastore.get(
                        fqid_from_collection_and_id("meeting_user", old_to_muser_id),
                        ["user_id"],
                        use_changed_models=False,
                        raise_exception=False,
                        lock_result=False,
                    ).get("user_id")
                )
            ):
                instance_information.append(
                    (
                        "Vote delegation canceled in meeting {}",
                        fqid_from_collection_and_id("meeting", meeting_id),
                    )
                )
                self.add_entries_to_history_information(
                    information,
                    [
                        (
                            "Proxy voting rights removed in meeting {}",
                            fqid_from_collection_and_id("meeting", meeting_id),
                        )
                    ],
                    for_user_id=old_to_user_id,
                )
            if instance["vote_delegated_to_id"]:
                to_user_id = self.datastore.get(
                    fqid_from_collection_and_id(
                        "meeting_user", instance["vote_delegated_to_id"]
                    ),
                    ["user_id"],
                    use_changed_models=True,
                    lock_result=False,
                )["user_id"]
                instance_information.append(
                    (
                        "Vote delegated to {} in meeting {}",
                        fqid_from_collection_and_id("user", to_user_id),
                        fqid_from_collection_and_id("meeting", meeting_id),
                    )
                )
                self.add_entries_to_history_information(
                    information,
                    [
                        (
                            "Proxy voting rights received in meeting {}",
                            fqid_from_collection_and_id("meeting", meeting_id),
                        )
                    ],
                    for_user_id=to_user_id,
                )
        if "vote_delegations_from_ids" in instance:
            new_delegations = set(instance.get("vote_delegations_from_ids", []))
            old_delegations = set(db_instance.get("vote_delegations_from_ids", []))
            added = new_delegations.difference(old_delegations)
            removed = old_delegations.difference(new_delegations)
            if removed:
                instance_information.append(
                    (
                        "Proxy voting rights removed in meeting {}",
                        fqid_from_collection_and_id("meeting", meeting_id),
                    )
                )
                for muser_id in removed:
                    self.add_entries_to_history_information(
                        information,
                        [
                            (
                                "Vote delegation canceled in meeting {}",
                                fqid_from_collection_and_id("meeting", meeting_id),
                            )
                        ],
                        for_meeting_user_id=muser_id,
                    )
            if added:
                db_added = [
                    date
                    for date in self.datastore.get_many(
                        [
                            GetManyRequest(
                                "meeting_user",
                                list(added),
                                ["vote_delegated_to_id", "user_id"],
                            )
                        ],
                        use_changed_models=False,
                        lock_result=False,
                    )["meeting_user"].values()
                    if date.get("vote_delegated_to_id")
                ]
                for date in db_added:
                    self.add_entries_to_history_information(
                        information,
                        [
                            (
                                "Vote delegation canceled in meeting {}",
                                fqid_from_collection_and_id("meeting", meeting_id),
                            )
                        ],
                        for_user_id=date["user_id"],
                    )
                    self.add_entries_to_history_information(
                        information,
                        [
                            (
                                "Proxy voting rights removed in meeting {}",
                                fqid_from_collection_and_id("meeting", meeting_id),
                            )
                        ],
                        for_meeting_user_id=date["vote_delegated_to_id"],
                    )
                instance_information.append(
                    (
                        "Proxy voting rights received in meeting {}",
                        fqid_from_collection_and_id("meeting", meeting_id),
                    )
                )
                for muser_id in added:
                    self.add_entries_to_history_information(
                        information,
                        [
                            (
                                "Vote delegated to {} in meeting {}",
                                fqid_from_collection_and_id("user", user_id),
                                fqid_from_collection_and_id("meeting", meeting_id),
                            )
                        ],
                        for_meeting_user_id=muser_id,
                    )
