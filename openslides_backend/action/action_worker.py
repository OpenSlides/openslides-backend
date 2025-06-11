import logging
import threading
from enum import StrEnum
from http import HTTPStatus
from time import sleep, time
from typing import Any, cast

from gunicorn.http.message import Request
from gunicorn.http.wsgi import Response
from gunicorn.workers.gthread import ThreadWorker

from openslides_backend.services.database.extended_database import ExtendedDatabase
from openslides_backend.services.postgresql.db_connection_handling import (
    env,
    get_new_os_conn,
)
from openslides_backend.shared.patterns import fqid_from_collection_and_id

# from ..services.datastore.interface import DatastoreService
from ..shared.exceptions import ActionException, DatabaseException
from ..shared.interfaces.event import Event, EventType
from ..shared.interfaces.logging import LoggingModule
from ..shared.interfaces.write_request import WriteRequest
from .action_handler import ActionHandler
from .util.typing import ActionsResponse, Payload


class ActionWorkerState(StrEnum):
    RUNNING = "running"
    END = "end"
    ABORTED = "aborted"


def handle_action_in_worker_thread(
    payload: Payload,
    user_id: int,
    is_atomic: bool,
    handler: ActionHandler,
    internal: bool = False,
) -> ActionsResponse:
    logger = handler.logging.getLogger(__name__)
    lock = threading.Lock()
    try:
        action_names = ",".join(elem.get("action", "") for elem in payload)
    except Exception:
        action_names = "Cannot be determined"
    action_worker_writing = ActionWorkerWriting(user_id, handler.logging, action_names)
    action_worker_thread = ActionWorker(
        payload,
        user_id,
        is_atomic,
        handler,
        lock,
        internal,
    )
    timeout = float(handler.env.OPENSLIDES_BACKEND_THREAD_WATCH_TIMEOUT)
    if timeout == -2:
        # do not use action workers at all
        action_worker_thread.run()
        return action_worker_thread.response

    curr_thread = cast(OSGunicornThread, threading.current_thread())
    curr_thread.action_worker_writing = action_worker_writing
    curr_thread.action_worker_thread = action_worker_thread
    action_worker_thread.start()
    while not action_worker_thread.started:
        sleep(0.001)  # The action_worker_thread should gain the lock and NOT this one

    if lock.acquire(timeout=timeout):
        lock.release()
        if hasattr(action_worker_thread, "exception"):
            raise action_worker_thread.exception
        if hasattr(action_worker_thread, "response"):
            return action_worker_thread.response
        msg = (
            "Action request ended with unknown reason, "
            "probably an unexpected timeout!"
        )
        logger.error(msg)
        raise ActionException(msg)

    with get_new_os_conn() as conn:
        extended_db = ExtendedDatabase(conn, handler.logging, env)
        message = action_worker_writing.initial_action_worker_write(extended_db)
    return ActionsResponse(
        status_code=HTTPStatus.ACCEPTED.value,
        success=False,
        message=message,
        results=[
            [
                {
                    "fqid": action_worker_writing.fqid,
                    "name": action_worker_writing.action_names,
                    "written": action_worker_writing.written,
                }
            ]
        ],
    )


class ActionWorkerWriting:
    def __init__(
        self,
        user_id: int,
        logging: LoggingModule,
        action_names: str,
        # datastore: DatastoreService,
    ) -> None:
        self.user_id = user_id
        self.start_time = round(time())
        self.logger = logging.getLogger(__name__)
        self.action_names = action_names

        self.new_id: int | None = None
        self.fqid: str = "Still not set"
        self.written: bool = False

    def initial_action_worker_write(self, extended_db: ExtendedDatabase) -> str:
        current_time = round(time())
        if not self.new_id:
            self.new_id = extended_db.reserve_id(collection="action_worker")
            self.fqid = fqid_from_collection_and_id("action_worker", self.new_id)
        try:
            extended_db.write(
                WriteRequest(
                    events=[
                        Event(
                            type=EventType.Create,
                            fqid=self.fqid,
                            fields={
                                "id": self.new_id,
                                "name": self.action_names,
                                "state": ActionWorkerState.RUNNING,
                                "created": self.start_time,
                                "timestamp": current_time,
                                "user_id": self.user_id,
                            },
                        )
                    ],
                    user_id=self.user_id,
                    locked_fields={},
                )
            )
            extended_db.get(self.fqid, [], lock_result=False, use_changed_models=False)
            message = f"Action ({self.action_names}) lasts too long. {self.fqid} written to database. Get the result from database, when the job is done."
            self.written = True
        except DatabaseException as e:
            message = f"Action ({self.action_names}) lasts too long, exception on writing {self.fqid}: {e.message}. Get the result later from database."
        self.logger.info(f"action_worker: {message}")
        return message

    def continue_action_worker_write(self, extended_db: ExtendedDatabase) -> None:
        current_time = round(time())
        extended_db.write(
            WriteRequest(
                events=[
                    Event(
                        type=EventType.Update,
                        fqid=self.fqid,
                        fields={
                            "timestamp": current_time,
                        },
                    )
                ],
                user_id=self.user_id,
                locked_fields={},
            )
        )
        self.logger.debug(
            f"running action_worker '{self.fqid} {self.action_names}': {current_time}"
        )

    def final_action_worker_write(
        self, extended_db: ExtendedDatabase, action_worker_thread: "ActionWorker"
    ) -> None:
        current_time = round(time())
        state = ActionWorkerState.END
        if hasattr(action_worker_thread, "exception"):
            if isinstance(action_worker_thread.exception, ActionException):
                exception = action_worker_thread.exception
            else:
                exception = ActionException(str(action_worker_thread.exception))
            response = exception.get_json()
            self.logger.error(
                f"finish action_worker '{self.fqid}' ({self.action_names}) {current_time} with exception: {exception.message}"
            )
        elif hasattr(action_worker_thread, "response"):
            response = action_worker_thread.response
            self.logger.info(
                f"finish action_worker '{self.fqid}' ({self.action_names}): {current_time}"
            )
        else:
            exception = ActionException(
                "action_worker aborted without any specific message"
            )
            state = ActionWorkerState.ABORTED
            response = exception.get_json()
            self.logger.error(
                f"aborted action_worker '{self.fqid}' ({self.action_names}) {current_time}: {exception.message}"
            )

        extended_db.write(
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
                user_id=self.user_id,
                locked_fields={},
            )
        )


class ActionWorker(threading.Thread):
    def __init__(
        self,
        payload: Payload,
        user_id: int,
        is_atomic: bool,
        handler: ActionHandler,
        lock: threading.Lock,
        internal: bool,
    ) -> None:
        super().__init__(name="action_worker")
        self.handler = handler
        self.payload = payload
        self.user_id = user_id
        self.is_atomic = is_atomic
        self.lock = lock
        self.internal = internal
        self.started: bool = False

    def run(self):  # type: ignore
        with self.lock:
            self.started = True
            try:
                self.response = self.handler.handle_request(
                    self.payload, self.user_id, self.is_atomic, self.internal
                )
            except Exception as exception:
                self.exception = exception


class OSGunicornThread(threading.Thread):
    """
    defined to still mypy
    """

    action_worker_writing: ActionWorkerWriting
    action_worker_thread: ActionWorker


def gunicorn_post_request(
    worker: ThreadWorker, req: Request, environ: dict[str, Any], resp: Response
) -> None:
    """
    gunicorn server hook, called after response of one request
    was send to client in the Thread of Gunicorns ThreadPool.

    if the resp.status_code is 202 (HTTPStatus.ACCEPTED.value) there is an
    action_thread created, which wasn't finished before the response
    to the client was send and should be kept alive until it ends.
    """
    if getattr(resp, "status_code", 200) != HTTPStatus.ACCEPTED.value:
        return

    try:
        curr_thread = cast(OSGunicornThread, threading.current_thread())
        action_worker = curr_thread.action_worker_thread
        action_worker_writing = curr_thread.action_worker_writing
        lock = action_worker.lock

        with get_new_os_conn() as conn:
            extended_db = ExtendedDatabase(conn, logging, env)
            while True:
                worker.tmp.notify()
                if action_worker_writing.written:
                    if lock.acquire(timeout=10):
                        action_worker_writing.final_action_worker_write(
                            extended_db, action_worker
                        )
                        lock.release()
                        break
                    else:
                        action_worker_writing.continue_action_worker_write(extended_db)
                else:
                    action_worker_writing.initial_action_worker_write(extended_db)
                conn.commit()
    except Exception as e:
        logger = logging.getLogger(__name__)
        msg = f"gunicorn_post_request:{str(e)}"
        logger.error(msg)
        raise ActionException(msg)


def gunicorn_worker_abort(worker: ThreadWorker) -> None:
    logger = logging.getLogger(__name__)
    logger.error(
        f"gunicorn_worker_abort: process_id:{worker.pid} parent_process:{worker.ppid}"
    )
