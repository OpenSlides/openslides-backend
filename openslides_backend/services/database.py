from typing import Tuple

import requests
import simplejson as json
from werkzeug.exceptions import InternalServerError


class Database:
    """
    Adapter to connect to (read-only) database.
    """

    def __init__(self, database_url: str) -> None:
        self.url = database_url
        self.headers = {"Content-Type": "application/json"}

    def get(self, *keys: str) -> Tuple[str, int]:
        """
        Fetches all data for given keys from database.
        """
        data = {"keys": keys}
        response = requests.get(self.url, data=json.dumps(data), headers=self.headers)
        if not response.ok:
            raise InternalServerError("Connection to database failed.")
        return response.json()["data"], response.json()["version"]
