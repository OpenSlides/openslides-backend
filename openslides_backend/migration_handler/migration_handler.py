from enum import Enum
from io import StringIO
from threading import Lock, Thread
from typing import Any, Dict, Optional

from datastore.migrations import MigrationException

from migrations import MigrationWrapper

from ..shared.exceptions import View400Exception
from ..shared.handlers.base_handler import BaseHandler


class MigrationProgressState(int, Enum):
    NO_MIGRATION_RUNNING = 0
    MIGRATION_RUNNING = 1
    MIGRATION_FINISHED = 2


class MigrationHandler(BaseHandler):

    lock = Lock()
    migration_running = False
    migrate_thread_stream: Optional[StringIO] = None
    migrate_thread_stream_can_be_closed: bool = False
    migrate_thread_exception: Optional[MigrationException] = None

    def handle_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not (command := payload.get("cmd")):
            raise View400Exception("No command provided")
        self.logger.info(f"Migration command: {command}")

        with MigrationHandler.lock:
            if command == "progress":
                if MigrationHandler.migration_running:
                    if MigrationHandler.migrate_thread_stream:
                        # Migration still running
                        return {
                            "status": MigrationProgressState.MIGRATION_RUNNING,
                            "output": MigrationHandler.migrate_thread_stream.getvalue(),
                        }
                    else:
                        raise RuntimeError("Invalid migration handler state")
                else:
                    if MigrationHandler.migrate_thread_stream:
                        # Migration finished and the full output can be returned. Do not remove the
                        # output in case the response is lost and must be delivered again, but set
                        # flag that it can be removed.
                        MigrationHandler.migrate_thread_stream_can_be_closed = True
                        # handle possible exception
                        if MigrationHandler.migrate_thread_exception:
                            exception_data = {
                                "exception": str(
                                    MigrationHandler.migrate_thread_exception
                                )
                            }
                        else:
                            exception_data = {}
                        return {
                            "status": MigrationProgressState.MIGRATION_FINISHED,
                            "output": MigrationHandler.migrate_thread_stream.getvalue(),
                            **exception_data,
                        }
                    else:
                        # Nothing to report
                        return {
                            "status": MigrationProgressState.NO_MIGRATION_RUNNING,
                        }

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
            MigrationHandler.migrate_thread_stream = StringIO()
            if command in ("migrate", "finalize"):
                thread = Thread(
                    target=self.execute_migrate_command, args=[command, verbose]
                )
                thread.start()
                return {
                    "status": MigrationProgressState.MIGRATION_RUNNING,
                    "output": MigrationHandler.migrate_thread_stream.getvalue(),
                }
            else:
                # short-running commands can just be executed directly
                self.execute_migrate_command(command, verbose)
                if MigrationHandler.migrate_thread_exception:
                    raise View400Exception(
                        str(MigrationHandler.migrate_thread_exception),
                        {"output": self.close_migrate_thread_stream()},
                    )
                else:
                    return {
                        "output": self.close_migrate_thread_stream(),
                    }

    def execute_migrate_command(self, command: str, verbose: bool) -> None:
        MigrationHandler.migration_running = True
        handler = MigrationWrapper(verbose, self.write_line)
        try:
            handler.execute_command(command)
        except MigrationException as e:
            MigrationHandler.migrate_thread_exception = e
            self.logger.exception(e)
        finally:
            MigrationHandler.migration_running = False

    def write_line(self, message: str) -> None:
        assert MigrationHandler.migrate_thread_stream
        MigrationHandler.migrate_thread_stream.write(message + "\n")

    @classmethod
    def close_migrate_thread_stream(cls) -> str:
        assert (stream := MigrationHandler.migrate_thread_stream)
        output = stream.getvalue()
        stream.close()
        MigrationHandler.migrate_thread_stream = None
        MigrationHandler.migrate_thread_stream_can_be_closed = False
        MigrationHandler.migrate_thread_exception = None
        return output
