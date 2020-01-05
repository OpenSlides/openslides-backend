from typing import Any, Dict, List, Tuple

import requests
import simplejson as json
from werkzeug.exceptions import InternalServerError

from .. import logging
from ..utils.types import Collection, FullQualifiedId

logger = logging.getLogger(__name__)


class DatabaseAdapter:
    """
    Adapter to connect to (read-only) database.
    """

    def __init__(self, database_url: str) -> None:
        self.url = database_url
        self.headers = {"Content-Type": "application/json"}

    def get(self, fqid: FullQualifiedId, mapped_fields: List[str] = None) -> None:
        data = {
            "command": "get",
            "parameters": {"fqid": str(fqid), "mapped_fields": mapped_fields},
        }
        logger.debug(f"Start request to database with the following data: {data}")
        response = requests.get(self.url, data=json.dumps(data), headers=self.headers)
        if not response.ok:
            if response.status_code >= 500:
                raise InternalServerError("Connection to database failed.")
            if response.json().get("error") == "ModelDoesNotExist":
                pass
            else:
                pass
            # TODO: Check codes and raise error (ModelDoesNotExist, ModelLocked, ModelDoesExist, InvalidFormat, ModelNotDeleted, MeetingIdMissing)
        else:
            pass
            # Get data and position from db

    def getMany(
        self, collection: Collection, ids: List[int], mapped_fields: List[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        data = {
            "command": "getMany",
            "parameters": {
                "collection": str(collection),
                "ids": ids,
                "mapped_fields": mapped_fields,
            },
        }
        logger.debug(f"Start request to database with the following data: {data}")
        response = requests.get(self.url, data=json.dumps(data), headers=self.headers)
        print(response)  # TODO: Use response
        return ([{"id": 42, "fields": {"foo": "bar"}}], 0)

    def getId(self, collection: Collection) -> Tuple[int, int]:
        data = {"command": "getId", "parameters": {"collection": str(collection)}}
        logger.debug(f"Start request to database with the following data: {data}")
        response = requests.get(self.url, data=json.dumps(data), headers=self.headers)
        print(response)  # TODO: Use response
        return (0, 0)
