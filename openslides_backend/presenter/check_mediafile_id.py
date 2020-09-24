from typing import Any

import fastjsonschema

from ..models.models import Mediafile
from ..shared.patterns import FullQualifiedId
from ..shared.schema import schema_version
from .base import BasePresenter
from .presenter import register_presenter

check_mediafile_id_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "check_mediafile_id data",
        "description": "Schema to validate the check_mediafile_id presenter data.",
        "properties": {"mediafile_id": {"type": "integer", "minimum": 1}},
        "required": ["mediafile_id"],
        "additionalProperties": False,
    }
)


@register_presenter("check_mediafile_id")
class CheckMediafileId(BasePresenter):
    """
    Check, if a mediafile can be accessed. Retrieve the filename, if access is granted.
    """

    schema = check_mediafile_id_schema

    def get_result(self) -> Any:
        mediafile = self.datastore.get(
            FullQualifiedId(Mediafile.collection, self.data["mediafile_id"]),
            mapped_fields=["filename", "is_directory"],
        )

        if not mediafile or mediafile["is_directory"]:
            return {"ok": False}

        # TODO: Call to the permission service.

        return {"ok": True, "filename": mediafile["filename"]}
