from enum import StrEnum
from io import StringIO
from threading import Lock, Thread
from typing import Any

from ..shared.exceptions import View400Exception
from ..shared.handlers.base_handler import BaseHandler
from ..shared.interfaces.env import Env
from ..shared.interfaces.logging import LoggingModule
from ..shared.interfaces.services import Services
from . import MigrationWrapper

# from openslides_backend.migrations import MigrationState as DatastoreMigrationState


# Amount of time that should be waited for a result from the migrate thread before returning an empty result
THREAD_WAIT_TIME = 0.2


class MigrationState(StrEnum):
    """
    All possible migration states, ordered by priority. E.g. a running migration implicates that
    migrations are required and required migration implicates that finalization is also required.
    """
    MIGRATION_RUNNING = "migration_running"
    MIGRATION_REQUIRED = "migration_required"
    FINALIZATION_REQUIRED = "finalization_required"
    NO_MIGRATION_REQUIRED = "no_migration_required"


class MigrationCommand(StrEnum):
    MIGRATE = "migrate"
    FINALIZE = "finalize"
    RESET = "reset"
    STATS = "stats"


class MigrationHandler(BaseHandler):
    lock = Lock()
    migration_running = False
    migrate_thread_stream: StringIO | None = None
    migrate_thread_stream_can_be_closed: bool = False
    migrate_thread_exception: Exception | None = None

    def __init__(self, env: Env, services: Services, logging: LoggingModule) -> None:
        super().__init__(env, services, logging)
        self.migration_wrapper = MigrationWrapper(False, self.logger.info)

    def handle_request(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not (command := payload.get("cmd")):
            raise View400Exception("No command provided")
        self.logger.info(f"Migration command: {command}")

        with MigrationHandler.lock:
            if MigrationHandler.migration_running:
                raise View400Exception(
                    "Migration is running, only 'progress' command is allowed"
                )

            if MigrationHandler.migrate_thread_stream:
                if MigrationHandler.migrate_thread_stream_can_be_closed is False:
                    raise View400Exception(
                        "Last migration output not read yet. Please call 'progress' first."
                    )
                else:
                    self.close_migrate_thread_stream()

            verbose = payload.get("verbose", False)
            if command == "stats":
                stats = self.migration_wrapper.handler.get_stats()
                return {
                    "stats": stats,
                }
            elif command in iter(MigrationCommand):
                MigrationHandler.migrate_thread_stream = StringIO()
                thread = Thread(
                    target=self.execute_migrate_command, args=[command, verbose]
                )
                thread.start()
                thread.join(THREAD_WAIT_TIME)
                if thread.is_alive():
                    # Migration still running. Report current progress and return
                    return {
                        # "status": MigrationState.MIGRATION_RUNNING,
                        "output": MigrationHandler.migrate_thread_stream.getvalue(),
                    }
                else:
                    # Migration already finished/had nothing to do
                    return self.get_migration_result()
            else:
                raise View400Exception("Unknown command: " + command)

    def execute_migrate_command(self, command: str, verbose: bool) -> None:
        MigrationHandler.migration_running = True
        handler = MigrationWrapper(verbose, self.write_line)
        try:
            return handler.execute_command(command)
        except Exception as e:
            MigrationHandler.migrate_thread_exception = e
            self.logger.exception(e)
        finally:
            MigrationHandler.migration_running = False

    def handle_progress_command(self) -> dict[str, Any]:
        if MigrationHandler.migration_running:
            if MigrationHandler.migrate_thread_stream:
                # Migration still running
                return {
                    # "status": MigrationState.MIGRATION_RUNNING,
                    "output": MigrationHandler.migrate_thread_stream.getvalue(),
                }
            else:
                raise RuntimeError("Invalid migration handler state")
        else:
            return self.get_migration_result()

    def get_migration_result(self) -> dict[str, Any]:
        # stats = self.migration_wrapper.handler.get_stats()
        if MigrationHandler.migrate_thread_stream:
            # Migration finished and the full output can be returned. Do not remove the
            # output in case the response is lost and must be delivered again, but set
            # flag that it can be removed.
            MigrationHandler.migrate_thread_stream_can_be_closed = True
            # handle possible exception
            if MigrationHandler.migrate_thread_exception:
                exception_data = {
                    "exception": str(MigrationHandler.migrate_thread_exception)
                }
            else:
                exception_data = {}
            return {
                # "status": stats["status"],
                "output": MigrationHandler.migrate_thread_stream.getvalue(),
                **exception_data,
            }
        else:
            # Nothing to report
            return {
                # "status": stats["status"],
            }

    def write_line(self, message: str) -> None:
        assert (stream := MigrationHandler.migrate_thread_stream)
        stream.write(message + "\n")

    @classmethod
    def close_migrate_thread_stream(cls) -> str:
        assert (stream := MigrationHandler.migrate_thread_stream)
        output = stream.getvalue()
        stream.close()
        MigrationHandler.migrate_thread_stream = None
        MigrationHandler.migrate_thread_stream_can_be_closed = False
        MigrationHandler.migrate_thread_exception = None
        return output
