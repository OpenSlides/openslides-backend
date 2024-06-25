from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import (
    BaseRequestEvent,
    RequestCreateEvent,
    RequestUpdateEvent,
)


class Migration(BaseModelMigration):
    """
    This migration introduces the new gender model which enables
    custom gender names for non default genders.
    This requires to replace all gender strings in organization and
    user models to be replaced with the corresponding gender id.
    """

    target_migration_index = 55

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        gender_strings = self.reader.get("organization/1", ["genders"]).get(
            "genders", ""
        )
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
        users = self.reader.get_all("user", ["gender"])
        userids_for_gender: dict[str, list[int]] = {}
        # update users
        for user_id, user in users.items():
            if user.get("gender"):
                if gender_id := gender_strings.index(user.get("gender")) + 1:
                    events.append(
                        RequestUpdateEvent(
                            fqid_from_collection_and_id("user", user_id),
                            {"gender_id": gender_id, "gender": None},
                        )
                    )
                    if userids_for_gender.get(gender_id):
                        userids_for_gender[gender_id].append(user_id)
                    else:
                        userids_for_gender[gender_id] = [user_id]
        # create genders with back relation to users
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
