import os
from datetime import datetime
from decimal import Decimal
from json import dumps as json_dumps
from math import ceil
from typing import Any, cast
from zoneinfo import ZoneInfo

from psycopg import Cursor
from psycopg.rows import DictRow

from meta.dev.src.helper_get_names import HelperGetNames  # type: ignore # noqa
from openslides_backend.migrations.migration_helper import (
    OLD_TABLES,
    MigrationHelper,
    MigrationState,
)
from openslides_backend.migrations.migrations.base import BaseMigration
from openslides_backend.models.base import Model, model_registry
from openslides_backend.models.fields import (
    DecimalField,
    Field,
    GenericRelationListField,
    JSONField,
    OrganizationField,
    RelationListField,
    TimestampField,
)
from openslides_backend.models.models import *  # type: ignore # noqa # necessary to fill model_registry
from openslides_backend.shared.env import is_truthy

RELATION_LIST_FIELD_CLASSES = [RelationListField, GenericRelationListField]
ORIGIN_COLLECTIONS = [
]

class Migration(BaseMigration):
    @staticmethod
    def data_definition(curs: Cursor[DictRow]) -> None:
        curs.Execute("""
        CREATE TABLE blocked_sessions (
            session_id INTEGER PRIMARY KEY GENERATED ALWAYS AS IDENTITY,
        );""")
