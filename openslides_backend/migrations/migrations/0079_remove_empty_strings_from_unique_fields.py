from datastore.migrations import BaseModelMigration
from datastore.writer.core.write_request import BaseRequestEvent, RequestUpdateEvent

from openslides_backend.shared.patterns import fqid_from_collection_and_id

from ...shared.filters import And, FilterOperator


class Migration(BaseModelMigration):
    """
    This migration removes empty strings from fields that'll be unique in reldb": "

    Fields are
    * committee/external_id
    * group/external_id
    * meeting/external_id
    * mediafile/title
    * motion/number
    * option/text
    * user/member_number
    """

    collection_to_field: dict[str, str] = {
        "committee": "external_id",
        "group": "external_id",
        "meeting": "external_id",
        "mediafile": "title",
        "motion": "number",
        "option": "text",
        "user": "member_number",
    }
    target_migration_index = 80

    def migrate_models(self) -> list[BaseRequestEvent] | None:
        events: list[BaseRequestEvent] = []
        for collection, field in self.collection_to_field.items():
            filter_ = And(
                FilterOperator(field, "=", ""),
                FilterOperator("meta_deleted", "!=", True),
            )
            models = self.reader.filter(collection, filter_, ["id"])
            events.extend(
                [
                    RequestUpdateEvent(
                        fqid_from_collection_and_id(collection, id_), {field: None}
                    )
                    for id_ in models
                ]
            )
        return events
