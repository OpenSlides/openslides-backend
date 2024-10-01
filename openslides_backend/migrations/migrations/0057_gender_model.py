from collections import defaultdict

from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import (
    BaseRequestEvent,
    RequestCreateEvent,
    RequestUpdateEvent,
)


class Migration(BaseModelMigration):
    """
    This migration introduces the new gender model which enables custom gender names for non default genders.
    This requires to replace all gender strings in organization and user models to be replaced with the corresponding gender id.
    If the migration runs in memory then all gender information is left untouched since the import will still handle it as a string.
    """

    target_migration_index = 58

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        if not self.reader.is_in_memory_migration:
            users = self.reader.get_all("user", ["gender"])
            default_genders = ["male", "female", "diverse", "non-binary"]
            gender_strings = self.reader.get("organization/1", ["genders"]).get(
                "genders", ""
            )
            gender_strings = default_genders + [
                gender for gender in gender_strings if gender not in default_genders
            ]
            # update organization
            events.append(
                RequestUpdateEvent(
                    fqid_from_collection_and_id("organization", 1),
                    {
                        "gender_ids": [n + 1 for n in range(len(gender_strings))],
                        "genders": None,
                    },
                )
            )
            userids_for_gender = defaultdict(list)
            # update users
            for user_id, user in users.items():
                user_gender_string = user.get("gender", "")
                if user_gender_string in gender_strings:
                    gender_id = gender_strings.index(user_gender_string) + 1
                    events.append(
                        RequestUpdateEvent(
                            fqid_from_collection_and_id("user", user_id),
                            {"gender_id": gender_id, "gender": None},
                        )
                    )
                    userids_for_gender[gender_id].append(user_id)
                else:
                    events.append(
                        RequestUpdateEvent(
                            fqid_from_collection_and_id("user", user_id),
                            {"gender": None},
                        )
                    )
            for gender_id, gender in enumerate(gender_strings, start=1):
                events.append(
                    RequestCreateEvent(
                        fqid_from_collection_and_id("gender", gender_id),
                        {
                            "id": gender_id,
                            "name": gender,
                            "organization_id": 1,
                            "user_ids": userids_for_gender.get(gender_id),
                        },
                    )
                )
        return events
