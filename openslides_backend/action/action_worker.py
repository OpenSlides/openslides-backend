import threading
from http import HTTPStatus
from time import sleep, time

from openslides_backend.shared.patterns import (
    FullQualifiedId,
    fqid_from_collection_and_id,
    id_from_fqid,
)

from ..shared.exceptions import DatastoreException
from ..shared.interfaces.event import Event, EventType
from ..shared.interfaces.logging import LoggingModule
from ..shared.interfaces.services import Services
from ..shared.interfaces.write_request import WriteRequest
from .action_handler import ActionHandler
from .util.typing import ActionsResponse, Payload

THREAD_WATCH_TIMEOUT = 1.0


def handle_action_in_worker_thread(
    payload: Payload,
    user_id: int,
    is_atomic: bool,
    handler: ActionHandler,
) -> ActionsResponse:
    starttime = round(time())
    logger = handler.logging.getLogger(__name__)
    lock = threading.Lock()
    worker_thread = ActionWorker(payload, user_id, is_atomic, handler, lock)
    worker_thread.start()
    sleep(0.001)  # The worker_thread should gain the lock
    if not worker_thread.is_alive() or lock.acquire(timeout=THREAD_WATCH_TIMEOUT):
        if hasattr(worker_thread, "exception"):
            logger.debug("Action request finished with exception within timeout.")
            raise worker_thread.exception
        logger.debug("Action request finished successfully within timeout.")
        return worker_thread.response
    else:
        datastore = handler.services.datastore()
        with datastore.get_database_context():
            action_names = ",".join(elem.get("action", "") for elem in payload)
            current_time = round(time())
            new_id = datastore.reserve_id(collection="action_worker")
            fqid = fqid_from_collection_and_id("action_worker", new_id)
            try:
                datastore.write_action_worker(
                    WriteRequest(
                        events=[
                            Event(
                                type=EventType.Create,
                                fqid=fqid,
                                fields={
                                    "id": new_id,
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
                datastore.get(fqid, [], lock_result=False, use_changed_models=False)
                message = "Action lasts to long. Get the result from database, when the job is done."
                written = True
            except DatastoreException:
                message = f"Action lasts to long, action_worker still blocks writing {fqid}. Get the result later from database."
                written = False
            logger.debug(
                f"action_worker: WorkerThread not ready in thread_watch_timeout:{message}, written:{written}"
            )

        watcher_thread = WatcherThread(
            fqid,
            written,
            action_names,
            starttime,
            worker_thread,
            user_id,
            handler.services,
            lock,
            handler.logging,
        )
        watcher_thread.start()
        return ActionsResponse(
            status_code=HTTPStatus.ACCEPTED.value,
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
        lock: threading.Lock,
    ) -> None:
        super().__init__(name="action_worker")
        self.handler = handler
        self.payload = payload
        self.user_id = user_id
        self.is_atomic = is_atomic
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
        services: Services,
        lock: threading.Lock,
        logging: LoggingModule,
    ) -> None:
        super().__init__(name="watcher_thread")
        self.fqid = fqid
        self.written = written
        self.action_names = action_names
        self.starttime = starttime
        self.worker_thread = worker_thread
        self.user_id = user_id
        self.services = services
        self.lock = lock
        self.logger = logging.getLogger(__name__)

    def run(self):  # type: ignore
        datastore = self.services.datastore()
        while True:
            current_time = round(time())
            with datastore.get_database_context():
                if self.written:
                    if not self.worker_thread.is_alive() or self.lock.acquire(
                        timeout=10
                    ):
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
                        datastore.write_action_worker(
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
                        self.logger.debug(
                            f"*** timestamps end action_worker '{self.fqid} {self.action_names}': {current_time}"
                        )
                        break
                    else:
                        datastore.write_action_worker(
                            WriteRequest(
                                events=[
                                    Event(
                                        type=EventType.Update,
                                        fqid=self.fqid,
                                        fields={"timestamp": current_time},
                                    )
                                ],
                                information={
                                    self.fqid: [
                                        "timestamp during running action_worker"
                                    ]
                                },
                                user_id=self.user_id,
                                locked_fields={},
                            )
                        )
                        self.logger.debug(
                            f"timestamp during running action_worker '{self.fqid} {self.action_names}': {current_time}"
                        )
                else:
                    datastore.write_action_worker(
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
                    self.logger.debug(
                        f"timestamps first running action_worker '{self.fqid} {self.action_names}': {current_time}"
                    )
                    self.written = True
