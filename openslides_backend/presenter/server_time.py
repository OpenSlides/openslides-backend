import time
from typing import Any

from .base import BasePresenter
from .presenter import register_presenter


@register_presenter("server_time")
class ServerTime(BasePresenter):
    """
    ServerTime returns the system time (int seconds).
    """

    def get_result(self) -> Any:
        return {"server_time": int(time.time())}
