from typing import Any

import fastjsonschema

from ..models.mediafile import Mediafile
from ..shared.exceptions import PresenterException
from ..shared.filters import And, FilterOperator
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

get_mediafile_id_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "get_mediafile_id data",
        "description": "Schema to validate the get_mediafile_id presenter data.",
        "properties": {
            "meeting_id": {"type": "integer", "minimum": 1},
            "path": {"type": "string"},
        },
        "required": ["meeting_id", "path"],
        "additionalProperties": False,
    }
)


@register_presenter("get_mediafile_id")
class GetMediafileId(BasePresenter):
    """
    Retrieve an Id for the given mediafiel or None if it not exists or access is forbidden.
    """

    schema = get_mediafile_id_schema

    def get_result(self) -> Any:
        filter = And(
            FilterOperator("path", "=", self.data["path"]),
            FilterOperator("meeting_id", "=", self.data["meeting_id"]),
        )
        result = self.datastore.filter(
            collection=Mediafile.collection,
            filter=filter,
            mapped_fields=[
                "inherited_access_group_ids",
                "access_group_ids",
                "current_projector_ids",
            ],
        )
        if len(result) > 1:
            raise PresenterException("Multiple files with the given path found!")
        if len(result) == 0:
            return None

        id, mediafile = list(result.items())[0]

        # TODO: Gain access to user and check if user has permission to see
        # TODO: check if file is projected or is a special file (font/logo)

        return int(id)
