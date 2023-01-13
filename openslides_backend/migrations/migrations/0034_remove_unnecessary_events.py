from typing import List, Optional

from datastore.migrations.core.base_migration import BaseMigration
from datastore.migrations.core.events import (
    BaseEvent,
    DeleteFieldsEvent,
    ListUpdateEvent,
    UpdateEvent,
)


class Migration(BaseMigration):
    target_migration_index = 35

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> Optional[List[BaseEvent]]:
        old = (
            self.new_accessor.get_model(event.fqid)
            if self.new_accessor.model_exists(event.fqid)
            else {}
        )
        new_data = {}
        if isinstance(event, UpdateEvent):
            for field, value in event.data.items():
                if value != old.get(field):
                    new_data[field] = value
        elif isinstance(event, ListUpdateEvent):
            new_add = {}
            new_remove = {}
            for field, value in event.add.items():
                new_value = [el for el in value if el not in old.get(field, [])]
                if new_value:
                    new_add[field] = new_value
            for field, value in event.remove.items():
                new_value = [el for el in value if el in old.get(field, [])]
                if new_value:
                    new_remove[field] = new_value
            if new_add or new_remove:
                if new_add:
                    event.add = new_add
                if new_remove:
                    event.remove = new_remove
                return [event]
        elif isinstance(event, DeleteFieldsEvent):
            new_data = []
            for field in event.data:
                if field in old:
                    new_data.append(field)
        else:
            return None

        if new_data:
            event.data = new_data
            return [event]
        else:
            return []
