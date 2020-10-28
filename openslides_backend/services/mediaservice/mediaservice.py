from typing import Dict, Optional

import requests

from ...shared.exceptions import ActionException

UPLOAD_URL = "http://media:9006/internal/media/upload/"


class Mediaservice:
    """
    Mediaservice.
    """

    def upload(self, file: str, id: int, mimetype: str) -> Optional[Dict[str, str]]:
        payload = {"file": file, "id": id, "mimetype": mimetype}
        try:
            response = requests.post(UPLOAD_URL, json=payload)
        except Exception:
            raise ActionException("Connect to mediaservice failed.")
        if response.status_code != 200:
            raise ActionException(f"Mediaservice Error: {str(response.json())}")
        return response.json()
