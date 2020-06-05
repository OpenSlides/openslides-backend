from typing import Dict, List, Union

import openslides_backend.services.database.commands as commands
from openslides_backend.services.database.adapter.interface import GetManyRequest
from openslides_backend.services.database.engine import Engine
from openslides_backend.shared.filters import Filter
from openslides_backend.shared.interfaces import LoggingModule
from openslides_backend.shared.patterns import Collection, FullQualifiedId

from .interface import Aggregate, Count, Found, PartialModel


class Adapter:
    """
    Adapter to connect to (read-only) database.
    """

    position = 0

    def __init__(self, adapter: Engine, logging: LoggingModule) -> None:
        self.logger = logging.getLogger(__name__)
        self.adapter = adapter

    def get(
        self,
        fqid: FullQualifiedId,
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> PartialModel:
        command = commands.Get(fqid=fqid, mappedFields=mapped_fields)
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.get(command)
        self.set_min_position(response)
        return response

    def get_many(
        self,
        get_many_requests: List[GetManyRequest],
        mapped_fields: List[str] = None,
        position: int = None,
        get_deleted_models: int = None,
    ) -> Dict[Collection, Dict[int, PartialModel]]:
        command = commands.GetMany(
            get_many_requests=get_many_requests,
            mapped_fields=mapped_fields,
            position=position,
            get_deleted_models=get_deleted_models,
        )
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.get_many(command)
        self.set_min_position(response)
        return response

    def get_all(
        self,
        collection: Collection,
        mapped_fields: List[str] = None,
        get_deleted_models: int = None,
    ) -> List[PartialModel]:
        command = commands.GetAll(collection=collection, mapped_fields=mapped_fields)
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.get_all(command)
        self.set_min_position(response)
        return response

    def filter(
        self,
        collection: Collection,
        filter: Filter,
        meeting_id: int = None,
        mapped_fields: List[str] = None,
    ) -> List[PartialModel]:
        command = commands.Filter(collection=collection, filter=filter)
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.filter(command)
        self.set_min_position(response)
        return response

    def exists(self, collection: Collection, filter: Filter) -> Found:
        command = commands.Exists(collection=collection, filter=filter)
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.exists(command)
        self.set_min_position(response)
        return {"exists": response["exists"], "position": response["position"]}

    def count(self, collection: Collection, filter: Filter) -> Count:
        command = commands.Count(collection=collection, filter=filter)
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.count(command)
        self.set_min_position(response)
        return {"count": response["count"], "position": response["position"]}

    def min(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        command = commands.Min(
            collection=collection, filter=filter, field=field, type=type
        )
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.min(command)
        self.set_min_position(response)
        return response

    def max(
        self, collection: Collection, filter: Filter, field: str, type: str = None
    ) -> Aggregate:
        command = commands.Max(
            collection=collection, filter=filter, field=field, type=type
        )
        self.logger.debug(
            f"Start request to database with the following data: {command.data}"
        )
        response = self.adapter.max(command)
        self.set_min_position(response)
        return response

    def set_min_position(
        self,
        response: Union[
            PartialModel,
            Dict[Collection, Dict[int, PartialModel]],
            List[PartialModel],
            Found,
            Count,
            Aggregate,
        ],
    ) -> None:
        """
        Inspects result from database and calculates the minimum value of
        "meta_position" fields inside the result.
        """
        # TODO: Calculate this. At the moment we use a fix value here.
        position = 1

        if self.position == 0:
            self.position = position
        else:
            self.position = min(position, self.position)

    def getId(self, collection: Collection) -> int:
        raise RuntimeError("This method has to be fixed.")
