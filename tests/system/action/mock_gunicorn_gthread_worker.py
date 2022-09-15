import threading
from typing import cast

from openslides_backend.action.action_worker import OSGunicornThread


class Tmp:
    @staticmethod
    def notify() -> None:
        pass


def getMockGunicornThreadWorker() -> OSGunicornThread:
    thread = cast(OSGunicornThread, threading.current_thread())
    thread.tmp = Tmp()
    return thread
