import threading
from time import sleep, time

from openslides_backend.shared.patterns import (
    FullQualifiedId,
    fqid_from_collection_and_id,
    id_from_fqid,
)

from ..shared.exceptions import DatastoreException
from ..shared.interfaces.event import Event, EventType
from ..shared.interfaces.write_request import WriteRequest
from .action_handler import ActionHandler
from .util.typing import ActionsResponse, Payload


def handle_action_in_worker_thread(
    payload: Payload,
    user_id: int,
    is_atomic: bool,
    handler: ActionHandler,
    thread_watch_timeout: int,
) -> ActionsResponse:
    starttime = round(time())
    lock = threading.Lock()
    worker_thread = ActionWorker(
        payload, user_id, is_atomic, handler, thread_watch_timeout, lock
    )
    worker_thread.start()
    sleep(0.001)  # The worker_thread should gain the lock
    if lock.acquire(timeout=thread_watch_timeout):
        if hasattr(worker_thread, "exception"):
            raise worker_thread.exception
        return worker_thread.response
    else:
        action_names = ",".join(elem.get("action", "") for elem in payload)
        current_time = round(time())
        new_ids = handler.datastore.reserve_ids(collection="action_worker", amount=1)
        fqid = fqid_from_collection_and_id("action_worker", new_ids[0])
        try:
            handler.datastore.write(
                WriteRequest(
                    events=[
                        Event(
                            type=EventType.Create,
                            fqid=fqid,
                            fields={
                                "id": new_ids[0],
                                "name": action_names,
                                "state": "running",
                                "created": starttime,
                                "timestamp": current_time,
                            },
                        )
                    ],
                    information={fqid: ["create action_worker"]},
                    user_id=user_id,
                    locked_fields={},
                )
            )
            handler.datastore.get(fqid, [], lock_result=False, use_changed_models=False)
            message = "Action lasts to long. Get the result from database, when the job is done."
            written = True
        except DatastoreException:
            message = f"Action lasts to long, action_worker still blocks writing {fqid}. Get the result later from database."
            written = False

        watcher_thread = WatcherThread(
            fqid,
            written,
            action_names,
            starttime,
            worker_thread,
            user_id,
            handler,
            lock,
        )
        watcher_thread.start()
        return ActionsResponse(
            success=False,
            message=message,
            results=[[{"fqid": fqid, "name": action_names, "written": written}]],
        )


class ActionWorker(threading.Thread):
    def __init__(
        self,
        payload: Payload,
        user_id: int,
        is_atomic: bool,
        handler: ActionHandler,
        thread_watch_time: int,
        lock: threading.Lock,
    ) -> None:
        super().__init__(name="action_worker")
        self.handler = handler
        self.payload = payload
        self.user_id = user_id
        self.is_atomic = is_atomic
        self.thread_watch_time = thread_watch_time
        self.lock = lock

    def run(self):  # type: ignore
        with self.lock:
            try:
                self.response = self.handler.handle_request(
                    self.payload, self.user_id, self.is_atomic
                )
            except Exception as exception:
                self.exception = exception


class WatcherThread(threading.Thread):
    def __init__(
        self,
        fqid: FullQualifiedId,
        written: bool,
        action_names: str,
        starttime: int,
        worker_thread: ActionWorker,
        user_id: int,
        handler: ActionHandler,
        lock: threading.Lock,
    ) -> None:
        super().__init__(name="watcher_thread")
        self.fqid = fqid
        self.written = written
        self.action_names = action_names
        self.starttime = starttime
        self.worker_thread = worker_thread
        self.user_id = user_id
        self.handler = handler
        self.lock = lock

    def run(self):  # type: ignore
        while True:
            current_time = round(time())
            if self.written:
                if not self.worker_thread.is_alive() or self.lock.acquire(timeout=10):
                    state = "end"
                    if hasattr(self.worker_thread, "exception"):
                        response = {
                            "success": False,
                            "message": str(self.worker_thread.exception),
                            "action_error_index": 0,
                            "action_data_error_index": 0,
                        }
                    elif hasattr(self.worker_thread, "response"):
                        response = self.worker_thread.response
                    else:
                        state = "aborted"
                        response = {
                            "success": False,
                            "message": "action_worker aborted without any specific message",
                            "action_error_index": 0,
                            "action_data_error_index": 0,
                        }
                    self.handler.datastore.write(
                        WriteRequest(
                            events=[
                                Event(
                                    type=EventType.Update,
                                    fqid=self.fqid,
                                    fields={
                                        "state": state,
                                        "timestamp": current_time,
                                        "result": response,
                                    },
                                )
                            ],
                            information={self.fqid: ["finish action_worker"]},
                            user_id=self.user_id,
                            locked_fields={},
                        )
                    )
                else:
                    self.handler.datastore.write(
                        WriteRequest(
                            events=[
                                Event(
                                    type=EventType.Update,
                                    fqid=self.fqid,
                                    fields={"timestamp": current_time},
                                )
                            ],
                            information={
                                self.fqid: ["timestamp during running action_worker"]
                            },
                            user_id=self.user_id,
                            locked_fields={},
                        )
                    )
            else:
                self.handler.datastore.write(
                    WriteRequest(
                        events=[
                            Event(
                                type=EventType.Create,
                                fqid=self.fqid,
                                fields={
                                    "id": id_from_fqid(self.fqid),
                                    "name": self.action_names,
                                    "state": "running",
                                    "created": self.starttime,
                                    "timestamp": current_time,
                                },
                            )
                        ],
                        information={self.fqid: ["create action_worker"]},
                        user_id=self.user_id,
                        locked_fields={},
                    )
                )
                self.written = True
