import time

from ....shared.patterns import to_fqid
from ...generics.update import UpdateAction
from .update import ProjectorCountdownUpdate


class CountdownControl(UpdateAction):
    def control_countdown(self, countdown_id: int, action: str) -> None:
        countdown = self.datastore.get(
            to_fqid("projector_countdown", countdown_id),
            ["default_time"],
        )
        if action == "reset":
            running = False
            countdown_time = countdown["default_time"]
        elif action == "restart":
            running = True
            now = round(time.time())
            countdown_time = countdown["default_time"] + now
        else:
            raise NotImplementedError

        self.execute_other_action(
            ProjectorCountdownUpdate,
            [
                {
                    "id": countdown_id,
                    "running": running,
                    "countdown_time": countdown_time,
                }
            ],
        )
