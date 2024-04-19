from openslides_backend.migrations import (
    BaseEvent,
    BaseEventMigration,
    DeleteFieldsEvent,
    ListUpdateEvent,
    UpdateEvent,
)


class Migration(BaseEventMigration):
    target_migration_index = 35

    def migrate_event(
        self,
        event: BaseEvent,
    ) -> list[BaseEvent] | None:
        old = (
            self.new_accessor.get_model(event.fqid)
            if self.new_accessor.model_exists(event.fqid)
            else {}
        )
        if isinstance(event, UpdateEvent):
            new_data = {}
            for field, value in event.data.items():
                if value != old.get(field):
                    new_data[field] = value
            if new_data:
                event.data = new_data
                return [event]
        elif isinstance(event, ListUpdateEvent):
            new_add = {}
            new_remove = {}
            for field, value in event.add.items():
                old_value = old.get(field, [])
                assert isinstance(old_value, list)
                new_value = [el for el in value if el not in old_value]
                if new_value:
                    new_add[field] = new_value
            for field, value in event.remove.items():
                old_value = old.get(field, [])
                assert isinstance(old_value, list)
                new_value = [el for el in value if el in old_value]
                if new_value:
                    new_remove[field] = new_value
            if new_add or new_remove:
                if new_add:
                    event.add = new_add
                if new_remove:
                    event.remove = new_remove
                return [event]
        elif isinstance(event, DeleteFieldsEvent):
            new_fields = []
            for field in event.data:
                if field in old:
                    new_fields.append(field)
            if new_fields:
                event.data = new_fields
                return [event]
        else:
            return None
        return []
