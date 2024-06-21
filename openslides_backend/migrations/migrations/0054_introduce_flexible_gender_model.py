from datastore.migrations import BaseModelMigration
from datastore.shared.util import fqid_from_collection_and_id
from datastore.writer.core import BaseRequestEvent, RequestUpdateEvent, RequestCreateEvent

from ...shared.filters import FilterOperator


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
        #Get genders. If None we are migrating our database from string based genders. Create genders from "genders" field.
        if gender_strings := self.reader.get("organization/1", ["genders"]).get("genders"):
            for list_pos, gender_name in enumerate(gender_strings, start=1):
                genders[list_pos] = {"name": gender_name}
            for gender_id, gender in genders.items():
                events.append(
                    RequestCreateEvent(
                        fqid_from_collection_and_id("gender", gender_id), {"id": gender_id, "name": gender.get("name"), "organization_id": 1}
                    )
                )
            #update organization
            events.append(
                RequestUpdateEvent(
                    fqid_from_collection_and_id("organization", 1), 
                    {
                        "gender_ids": [n + 1 for n in range(len(gender_strings))], 
                        "genders": None
                    }
                )
            )
            users = self.reader.get_all("user", ["gender"])
            name_to_gender_id = {gender.get("name"): gender_id for gender_id, gender in genders.items()}
            userids_to_gender = {}
            #update users
            for user_id, user in users.items():
                if gender_id := name_to_gender_id.get(user.get("gender")):# and #if users gender is present and
                    if not [g_dict for g_dict in genders.values() if user_id in g_dict.get("user_ids", [])]: #if user is not referenced inside a gender 
                        events.append(
                            RequestUpdateEvent(
                                fqid_from_collection_and_id("user", user_id),
                                {
                                    "gender_id": gender_id,
                                    "gender": None
                                }
                            )
                        )
                        if userids_to_gender.get(gender_id):
                            userids_to_gender[gender_id] = userids_to_gender[gender_id] + [user_id]
                        else:
                            userids_to_gender[gender_id] = [user_id]
                    else:
                        pass
            #update genders with back relation to users TODO: one creation no update + create default genders
            for gender_id, user_ids in userids_to_gender.items():
                events.append(
                    RequestUpdateEvent(
                        fqid_from_collection_and_id("gender", gender_id),
                        fields = {},
                        list_fields = {
                            "add": {
                                "user_ids": user_ids
                            }
                        }
                    )
                )
        return events
