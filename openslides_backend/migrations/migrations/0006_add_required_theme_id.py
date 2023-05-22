from typing import List, Optional

from datastore.migrations import BaseEvent, BaseEventMigration, CreateEvent, UpdateEvent

ONE_ORGANIZATION_FQID = "organization/1"


class Migration(BaseEventMigration):
    target_migration_index = 7

    def position_init(self) -> None:
        self.update_theme_id = False

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        if event.fqid != ONE_ORGANIZATION_FQID:
            return None

        if isinstance(event, CreateEvent):
            self.update_theme_id = True
            return [
                event,
                CreateEvent(
                    "theme/1",
                    {
                        "id": 1,
                        "name": "OpenSlides Blue",
                        "primary_500": "#317796",
                        "accent_500": "#2196f3",
                        "warn_500": "#f06400",
                        "organization_id": 1,
                        "theme_for_organization_id": 1,
                    },
                ),
            ]
        return None

    def get_additional_events(self) -> Optional[List[BaseEvent]]:
        if self.update_theme_id:
            return [
                UpdateEvent(ONE_ORGANIZATION_FQID, {"theme_id": 1, "theme_ids": [1]})
            ]
        return None
