from typing import Optional, Tuple

import requests

from ...shared.exceptions import DatastoreException
from ...shared.interfaces.logging import LoggingModule


class HTTPEngine:
    """
    HTTP implementation of the Engine interface
    """

    READER_ENDPOINTS = [
        "get",
        "get_many",
        "get_all",
        "filter",
        "exists",
        "count",
        "min",
        "max",
    ]
    WRITER_ENDPOINTS = ["reserve_ids", "write", "truncate_db"]

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

    def retrieve(self, endpoint: str, data: Optional[str]) -> Tuple[bytes, int]:
        # TODO: Check and test this error handling.
        if endpoint in self.READER_ENDPOINTS:
            base_url = self.datastore_reader_url
        elif endpoint in self.WRITER_ENDPOINTS:
            base_url = self.datastore_writer_url
        else:
            raise ValueError(f"Endpoint {endpoint} does not exist.")
        url = "/".join((base_url, endpoint))

        try:
            response = requests.post(url=url, data=data, headers=self.headers)
        except requests.exceptions.ConnectionError as e:
            error_message = f"Cannot reach the datastore service on {url}. Error: {e}"
            raise DatastoreException(error_message)
        return response.content, response.status_code
