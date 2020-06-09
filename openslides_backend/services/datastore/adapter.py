from typing import Dict, List, Sequence, Union

import requests
import simplejson as json
from typing_extensions import TypedDict

from ...shared.filters import Filter
from ...shared.interfaces import Event, LoggingModule, WriteRequestElement
from ...shared.patterns import (
    KEYSEPARATOR,
    Collection,
    FullQualifiedField,
    FullQualifiedId,
)
from . import commands
from .http_engine import HTTPEngine as Engine
from .interface import Aggregate, Count, Found, PartialModel


class Adapter:
    """
    Adapter to connect to readable and writeable datastore.
    """

    # The key of this dictionary is a stringified FullQualifiedId or FullQualifiedField
    position: Dict[str, int]

    def __init__(self, engine: Engine, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.engine = engine
        self.position = {}  # TODO: Rename to locked_fields

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> PartialModel:
        command = commands.Get(fqid=fqid, mappedFields=mapped_fields)
        self.logger.debug(
            f"Start GET request to datastore with the following data: {command.data}"
        )
        response = self.engine.get(command)
        position = response.get("meta_position")
        if position is not None:
            self.set_min_position(fqid, position)
        return response

    def get_many(
        self,
        get_many_requests: List[commands.GetManyRequest],
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> Dict[FullQualifiedId, PartialModel]:
        command = commands.GetMany(
            get_many_requests=get_many_requests,
            mapped_fields=mapped_fields,
            position=position,
            get_deleted_models=get_deleted_models,
        )
        self.logger.debug(
            f"Start GET_MANY request to datastore with the following data: {command.data}"
        )
        response = self.engine.get_many(command)
        result = {}
        for key, value in response.items():
            collection, id = key.split(KEYSEPARATOR)
            fqid = FullQualifiedId(collection=Collection(collection), id=int(id))
            result[fqid] = value
            position = value.get("meta_position")
            if position is not None:
                self.set_min_position(fqid, position)
        return result

    def get_all(
        self,
        collection: Collection,
        mapped_fields: List[str] = None,
        get_deleted_models: int = None,
    ) -> List[PartialModel]:
        # TODO: Check the return value of this method. The interface docs say
        # something else.
        command = commands.GetAll(collection=collection, mapped_fields=mapped_fields)
        self.logger.debug(
            f"Start GET_ALL request to datastore with the following data: {command.data}"
        )
        response = self.engine.get_all(command)
        for item in response:
            position = item.get("meta_position")
            item_id = item.get("id")
            if position is not None and id is not None:
                fqid = FullQualifiedId(collection=collection, id=item_id)
                self.set_min_position(fqid, position)
        return response

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        meeting_id: int = None,
        mapped_fields: List[str] = None,
    ) -> List[PartialModel]:
        # TODO: Check the return value of this method. The interface docs say
        # something else.
        command = commands.Filter(collection=collection, filter=filter)
        self.logger.debug(
            f"Start FILTER request to datastore with the following data: {command.data}"
        )
        response = self.engine.filter(command)
        for item in response:
            position = item.get("meta_position")
            item_id = item.get("id")
            if position is not None and id is not None:
                fqid = FullQualifiedId(collection=collection, id=item_id)
                self.set_min_position(fqid, position)
        return response

    def exists(self, collection: Collection, filter: Filter) -> Found:
        # Attention: We do not handle the position result of this request. You
        # have to do this manually.
        command = commands.Exists(collection=collection, filter=filter)
        self.logger.debug(
            f"Start EXISTS request to datastore with the following data: {command.data}"
        )
        response = self.engine.exists(command)
        return {"exists": response["exists"], "position": response["position"]}

    def count(self, collection: Collection, filter: Filter) -> Count:
        # Attention: We do not handle the position result of this request. You
        # have to do this manually.
        command = commands.Count(collection=collection, filter=filter)
        self.logger.debug(
            f"Start COUNT request to datastore with the following data: {command.data}"
        )
        response = self.engine.count(command)
        return {"count": response["count"], "position": response["position"]}

    def min(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        # TODO: This method does nit reflect the position of the fetched objects.
        command = commands.Min(
            collection=collection, filter=filter, field=field, type=type
        )
        self.logger.debug(
            f"Start MIN request to datastore with the following data: {command.data}"
        )
        response = self.engine.min(command)
        return response

    def max(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        # TODO: This method does nit reflect the position of the fetched objects.
        command = commands.Max(
            collection=collection, filter=filter, field=field, type=type
        )
        self.logger.debug(
            f"Start MAX request to datastore with the following data: {command.data}"
        )
        response = self.engine.max(command)
        return response

    def set_min_position(
        self, key: Union[FullQualifiedId, FullQualifiedField], position: int,
    ) -> None:
        """
        """
        # TODO: Rename this method and add docstring.
        current_position = self.position.get(str(key))
        if current_position is None:
            new_position = position
        else:
            new_position = min(position, current_position)
        self.position[str(key)] = new_position

    def reserve_ids(self, collection: Collection, amount: int) -> Sequence[int]:
        self.logger.debug(
            f"Start RESERVE_IDS request to datastore with the following data: "
            f"Collection: {collection}, Amount: {amount}"
        )

        # TODO: Do not use hardcoded stuff here.
        payload = json.dumps({"collection": str(collection), "amount": amount})
        headers = {"Content-Type": "application/json"}
        response = requests.post(
            "http://localhost:9003/internal/datastore/writer/reserve_ids",
            data=payload,
            headers=headers,
        )
        # TODO: Catch error if server does not respond.
        if not response.ok:
            raise RuntimeError("Bad")
        return response.json().get("ids")

    def reserve_id(self, collection: Collection) -> int:
        return self.reserve_ids(collection=collection, amount=1)[0]

    def write(self, write_requests: Sequence[WriteRequestElement]) -> None:
        headers = {"Content-Type": "application/json"}
        # TODO: Support multiple write_requests
        if len(write_requests) != 1:
            raise RuntimeError("Multiple or None write_requests not supported.")

        StringifiedWriteRequestElement = TypedDict(
            "StringifiedWriteRequestElement",
            {
                "events": List[Event],
                "information": Dict[str, List[str]],
                "user_id": int,
                "locked_fields": Dict[str, int],
            },
        )

        information = {}
        for fqid, value in write_requests[0]["information"].items():
            information[str(fqid)] = value

        stringified_write_request_element: StringifiedWriteRequestElement = {
            "events": write_requests[0]["events"],
            "information": information,
            "user_id": write_requests[0]["user_id"],
            "locked_fields": self.position,
        }
        # TODO: REMOVE locked_fields in business logic

        class MyEncoder(json.JSONEncoder):
            def default(self, o):  # type: ignore
                if isinstance(o, FullQualifiedId):
                    return str(o)
                return super().default(o)

        payload = json.dumps(stringified_write_request_element, cls=MyEncoder)
        response = requests.post(
            "http://localhost:9003/internal/datastore/writer/write",  # TODO: Do not hard code here.
            data=payload,
            headers=headers,
        )
        if not response.ok:
            raise RuntimeError("Something went wrong.")
