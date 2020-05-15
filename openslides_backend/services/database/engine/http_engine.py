import requests
import simplejson as json

from openslides_backend.shared.exceptions import DatabaseException
from openslides_backend.shared.interfaces import LoggingModule

from .interface import Command, EngineResponse


class HTTPEngine:
    """HTTP implementation of the Engine interface
    """

    def __init__(self, database_url: str, logging: LoggingModule):
        self.logger = logging.getLogger(__name__)
        self.url = database_url
        self.headers = {"Content-Type": "application/json"}

    def _retrieve(self, command_url: str, command: Command) -> EngineResponse:
        payload = json.dumps(command.data)
        response = requests.post(command_url, data=payload, headers=self.headers)
        if not response.ok:
            if response.status_code >= 500:
                raise DatabaseException("Connection to database failed.")
        error = None
        try:
            error = response.json().get("error")
        except:  # noqa: E722
            pass
        if error is not None:
            raise DatabaseException(error)
        return response.json()

    def get(self, command: Command) -> EngineResponse:
        command_url = f" {self.url}/get"  # noqa
        return self._retrieve(command_url, command)

    def getMany(self, command: Command) -> EngineResponse:
        command_url = f" {self.url}/get_many"  # noqa
        return self._retrieve(command_url, command)

    def getManyByFQIDs(self, command: Command) -> EngineResponse:
        command_url = f" {self.url}/get_many"  # noqa
        return self._retrieve(command_url, command)

    def getAll(self, command: Command) -> EngineResponse:
        command_url = f" {self.url}/get_all"
        return self._retrieve(command_url, command)

    def filter(self, command: Command) -> EngineResponse:
        command_url = f" {self.url}/filter"
        return self._retrieve(command_url, command)

    def exists(self, command: Command) -> EngineResponse:
        command_url = f" {self.url}/exists"
        return self._retrieve(command_url, command)

    def count(self, command: Command) -> EngineResponse:
        command_url = f" {self.url}/count"
        return self._retrieve(command_url, command)

    def min(self, command: Command) -> EngineResponse:
        command_url = f" {self.url}/min"
        return self._retrieve(command_url, command)

    def max(self, command: Command) -> EngineResponse:
        command_url = f" {self.url}/max"
        return self._retrieve(command_url, command)
