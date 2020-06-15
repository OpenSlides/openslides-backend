import requests
from simplejson.errors import JSONDecodeError  # type: ignore

from ...shared.exceptions import DatabaseException
from ...shared.interfaces import LoggingModule
from .interface import Command, EngineResponse


class HTTPEngine:
    """
    HTTP implementation of the Engine interface
    """

    def __init__(
        self,
        datastore_reader_url: str,
        datastore_writer_url: str,
        logging: LoggingModule,
    ):
        self.logger = logging.getLogger(__name__)
        self.datastore_reader_url = datastore_reader_url
        self.datastore_writer_url = datastore_writer_url
        self.headers = {"Content-Type": "application/json"}

    def _retrieve(self, command_url: str, command: Command) -> EngineResponse:
        # TODO: Check and test this error handling.
        try:
            response = requests.post(
                command_url, data=command.data, headers=self.headers
            )
        except requests.exceptions.ConnectionError as e:
            error_message = (
                f"Cannot reach the datastore service on {command_url}. Error: {e}"
            )
            self.logger.debug(error_message)
            raise DatabaseException(error_message)

        if len(response.content):
            try:
                body = response.json()
            except JSONDecodeError:
                error_message = (
                    "Bad response from datastore service. Body does not contain JSON."
                )
                self.logger.debug(error_message)
                raise DatabaseException(error_message)
        else:
            body = None
        self.logger.debug(f"Get repsonse: {body}")

        if not response.ok:
            error_message = f"Datastore service sends HTTP {response.status_code}."
            additional_error_message = body.get("error")
            if additional_error_message is not None:
                error_message = " ".join((error_message, str(additional_error_message)))
            self.logger.debug(error_message)
            raise DatabaseException(error_message)

        return body

    def get(self, command: Command) -> EngineResponse:
        command_url = f"{self.datastore_reader_url}/get"
        return self._retrieve(command_url, command)

    def get_many(self, command: Command) -> EngineResponse:
        command_url = f"{self.datastore_reader_url}/get_many"
        return self._retrieve(command_url, command)

    def get_all(self, command: Command) -> EngineResponse:
        command_url = f"{self.datastore_reader_url}/get_all"
        return self._retrieve(command_url, command)

    def filter(self, command: Command) -> EngineResponse:
        command_url = f"{self.datastore_reader_url}/filter"
        return self._retrieve(command_url, command)

    def exists(self, command: Command) -> EngineResponse:
        command_url = f"{self.datastore_reader_url}/exists"
        return self._retrieve(command_url, command)

    def count(self, command: Command) -> EngineResponse:
        command_url = f"{self.datastore_reader_url}/count"
        return self._retrieve(command_url, command)

    def min(self, command: Command) -> EngineResponse:
        command_url = f"{self.datastore_reader_url}/min"
        return self._retrieve(command_url, command)

    def max(self, command: Command) -> EngineResponse:
        command_url = f"{self.datastore_reader_url}/max"
        return self._retrieve(command_url, command)

    def reserve_ids(self, command: Command) -> EngineResponse:
        command_url = f"{self.datastore_writer_url}/reserve_ids"
        return self._retrieve(command_url, command)

    def write(self, command: Command) -> EngineResponse:
        command_url = f"{self.datastore_writer_url}/write"
        return self._retrieve(command_url, command)
