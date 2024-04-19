from openslides_backend.shared.typing import JSON

from .. import BaseEvent
from .add_fields_migration import AddFieldsMigration, Calculated


class AddFieldMigration(AddFieldsMigration):
    """
    This migration adds a new field to a collection with a given default value.
    """

    collection: str
    field: str
    default: JSON

    def __init__(self) -> None:
        super().__init__()
        self.defaults = {self.collection: {self.field: Calculated()}}

    def get_default(self, event: BaseEvent) -> JSON:
        """Can be overwritten for custom default values."""
        return self.default

    def get_default_for_field(self, event: BaseEvent, field: str) -> JSON:
        return self.get_default(event)
