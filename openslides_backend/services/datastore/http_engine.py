import requests

from ...shared.exceptions import DatastoreConnectionException
from ...shared.interfaces.logging import LoggingModule


class HTTPEngine:
    """
    HTTP implementation of the Engine interface
    """

    READER_ENDPOINTS = [
        "get",
        "get_many",
        "get_all",
        "get_everything",
        "filter",
        "exists",
        "count",
        "min",
        "max",
    ]
    WRITER_ENDPOINTS = [
        "reserve_ids",
        "write",
        "truncate_db",
        "delete_history_information",
        "write_without_events",
    ]

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

    def retrieve(self, endpoint: str, data: str | None) -> tuple[bytes | str, int]:
        """
        Throws 2 kinds of DatastoreConnectionException:
        1. If there is no valid endpoint given to build a URL
        2. If the datastore cannot be reached for unknown reasons
        Other exceptions from request.post are passed thru
        """
        # TODO: Check and test this error handling.
        if endpoint in self.READER_ENDPOINTS:
            base_url = self.datastore_reader_url
        elif endpoint in self.WRITER_ENDPOINTS:
            base_url = self.datastore_writer_url
        else:
            raise DatastoreConnectionException(f"Endpoint {endpoint} does not exist.")
        url = "/".join((base_url, endpoint))

        try:
            response = requests.post(url=url, data=data, headers=self.headers)
        except requests.exceptions.ConnectionError as e:
            error_message = f"Cannot reach the datastore service on {url}. Error: {e}"
            raise DatastoreConnectionException(error_message)
        return response.content, response.status_code
