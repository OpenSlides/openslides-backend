import mimetypes
from typing import Any

import fastjsonschema

from ..models.models import Resource
from ..shared.patterns import FullQualifiedId
from ..shared.schema import required_id_schema, schema_version
from .base import BasePresenter
from .presenter import register_presenter

check_resource_id_schema = fastjsonschema.compile(
    {
        "$schema": schema_version,
        "type": "object",
        "title": "check_resource_id data",
        "description": "Schema to validate the check_resource_id presenter data.",
        "properties": {"resource_id": required_id_schema},
        "required": ["resource_id"],
        "additionalProperties": False,
    }
)


@register_presenter("check_resource_id")
class CheckResourceId(BasePresenter):
    """
    Check, if a resource can be accessed. Retrieve the filename, if access is granted.
    """

    schema = check_resource_id_schema

    def get_result(self) -> Any:
        resource = self.datastore.get(
            FullQualifiedId(Resource.collection, self.data["resource_id"]),
            mapped_fields=["token", "mimetype"],
        )

        if not resource:
            return {"ok": False}

        extension = mimetypes.guess_extension(resource["mimetype"])
        if extension is None:
            return {"ok": False}
        filename = resource["token"] + extension

        return {"ok": True, "filename": filename}
