from copy import deepcopy

from ....shared.patterns import fqid_from_collection_and_id
from ....shared.typing import HistoryInformation
from ...action import Action


class MeetingUserHistoryMixin(Action):
    def get_history_information(self) -> HistoryInformation | None:
        information = {}

        # Scan the instances and collect the info for the history information
        # Copy instances first since they are modified
        for instance in deepcopy(self.instances):
            instance_information = []

            # Fetch the current instance from the db to diff with the given instance
            db_instance = self.datastore.get(
                fqid_from_collection_and_id(self.model.collection, instance["id"]),
                list(instance.keys()) + ["user_id", "meeting_id"],
                use_changed_models=False,
                raise_exception=False,
            )
            if not db_instance:
                continue
            user_id = db_instance["user_id"]
            meeting_id = db_instance["meeting_id"]

            # Compare db version with payload
            for field in list(instance.keys()):
                # Remove fields if equal
                if instance[field] == db_instance.get(field):
                    del instance[field]

            # meeting specific data
            update_fields = ["structure_level", "number", "vote_weight"]
            if any(field in instance for field in update_fields):
                instance_information.extend(
                    [
                        "Participant data updated in meeting {}",
                        fqid_from_collection_and_id("meeting", meeting_id),
                    ]
                )

            # groups
            if "group_ids" in instance:
                instance_group_ids = set(instance["group_ids"])
                db_group_ids = set(db_instance.get("group_ids", []))
                added = instance_group_ids - db_group_ids
                removed = db_group_ids - instance_group_ids

                # remove default groups
                meeting = self.datastore.get(
                    fqid_from_collection_and_id("meeting", meeting_id),
                    ["default_group_id"],
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
                instance_information.extend(group_information)

            if instance_information:
                information[fqid_from_collection_and_id("user", user_id)] = (
                    instance_information
                )
        return information
