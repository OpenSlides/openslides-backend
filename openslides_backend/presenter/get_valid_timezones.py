from typing import Any

import fastjsonschema
from psycopg import sql

from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

get_valid_timezones_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "get valid timezones",
        "description": "get valid timezones",
        "properties": {},
    }
)


@register_presenter("get_valid_timezones")
class GetValidTimezones(BasePresenter):
    """
    Returns all timezones allowed by the database.
    """

    schema = get_valid_timezones_schema

    def get_result(self) -> Any:
        timezones = self.datastore.execute_custom_select(
            sql.SQL("name, abbrev FROM pg_timezone_names")
        )
        return {tz["name"]: tz["abbrev"] for tz in timezones}
