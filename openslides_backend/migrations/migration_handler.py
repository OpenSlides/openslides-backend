import time
from enum import Enum
from io import StringIO
from threading import Lock, Thread
from typing import Any, Dict, Optional

from datastore.migrations import MigrationException

from migrations import MigrationWrapper

from ..shared.exceptions import View400Exception
from ..shared.handlers.base_handler import BaseHandler

# Amount of time that should be waited for a result from the migrate thread before returning an empty result
THREAD_WAIT_TIME = 0.1


class MigrationProgressState(int, Enum):
    NO_MIGRATION_RUNNING = 0
    MIGRATION_RUNNING = 1
    MIGRATION_FINISHED = 2


class MigrationHandler(BaseHandler):

    lock = Lock()
    migration_running = False
    migrate_thread_stream: Optional[StringIO] = None

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
                        # Migration finished, but last output was not read yet. Close stream and return result
                        output = self.close_migrate_thread_stream()
                        return {
                            "status": MigrationProgressState.MIGRATION_FINISHED,
                            "output": output,
                        }
                    else:
                        # Nothing to report
                        return {
                            "status": MigrationProgressState.NO_MIGRATION_RUNNING,
                            "message": "No migration running!",
                        }

            if MigrationHandler.migration_running:
                raise View400Exception(
                    "Migration is running, only 'progress' command is allowed"
                )

            if MigrationHandler.migrate_thread_stream:
                self.logger.warning(
                    "Deleting unread migration output:\n"
                    + self.close_migrate_thread_stream()
                )

            verbose = payload.get("verbose", False)
            MigrationHandler.migrate_thread_stream = StringIO()
            if command in ("migrate", "finalize"):
                thread = Thread(
                    target=self.execute_migrate_command, args=[command, verbose]
                )
                thread.start()
                thread.join(THREAD_WAIT_TIME)
                if thread.is_alive():
                    # Migration still running. Report current progress and return
                    return {
                        "status": MigrationProgressState.MIGRATION_RUNNING,
                        "output": MigrationHandler.migrate_thread_stream.getvalue(),
                    }
                else:
                    # Migration already finished/had nothing to do. Close stream and return all output
                    return {
                        "status": MigrationProgressState.MIGRATION_FINISHED,
                        "output": self.close_migrate_thread_stream(),
                    }
            else:
                # short-running commands can just be executed directy
                self.execute_migrate_command(command, verbose)
                return {
                    "output": self.close_migrate_thread_stream(),
                }

    def execute_migrate_command(self, command: str, verbose: bool) -> None:
        MigrationHandler.migration_running = True
        time.sleep(10)
        handler = MigrationWrapper(verbose, self.write_line)
        try:
            handler.execute_command(command)
        except MigrationException as e:
            raise View400Exception(str(e))
        MigrationHandler.migration_running = False

    def write_line(self, message: str) -> None:
        assert MigrationHandler.migrate_thread_stream
        MigrationHandler.migrate_thread_stream.write(message + "\n")

    def close_migrate_thread_stream(self) -> str:
        assert (stream := MigrationHandler.migrate_thread_stream)
        output = stream.getvalue()
        stream.close()
        MigrationHandler.migrate_thread_stream = None
        return output
