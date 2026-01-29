from datastore.migrations import BaseModelMigration
from datastore.writer.core.write_request import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id


class Migration(BaseModelMigration):
    """
    This migration removes the ids of non-existant or deleted meeting_users from group/meeting_user_ids
    """

    target_migration_index = 78
    model_to_field_and_target_model: dict[str, tuple[str, str]] = {
        "group": ("meeting_user_ids", "meeting_user"),
        "meeting": ("present_user_ids", "user"),
    }

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        all_existing_target_ids = {
            model: set(self.reader.get_all(data[1], ["id"]))
            for model, data in self.model_to_field_and_target_model.items()
        }
        all_existing_origins = {
            model: self.reader.get_all(model, [data[0]])
            for model, data in self.model_to_field_and_target_model.items()
        }
        events: list[BaseRequestEvent] = []
        for model, target_data in self.model_to_field_and_target_model.items():
            for id_, data in all_existing_origins[model].items():
                if remove_ids := set(data.get(target_data[0]) or []).difference(
                    all_existing_target_ids[model]
                ):
                    events.append(
                        RequestUpdateEvent(
                            fqid=fqid_from_collection_and_id(model, id_),
                            fields={},
                            list_fields={"remove": {target_data[0]: list(remove_ids)}},
                        )
                    )
        return events
