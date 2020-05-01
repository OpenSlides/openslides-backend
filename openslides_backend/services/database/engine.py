import requests
import simplejson as json

from openslides_backend.shared.interfaces import LoggingModule


class HTTPEngine:
    def __init__(self, database_url: str, logging: LoggingModule):
        self.logger = logging.getLogger(__name__)
        self.url = database_url
        self.headers = {"Content-Type": "application/json"}

    def get(self, data: object) -> requests.Response:
        return requests.get(self.url, data=json.dumps(data), headers=self.headers)
