from enum import Enum, auto
from time import time
from typing import cast

from openslides_backend.action.actions.speaker.speech_state import SpeechState
from openslides_backend.action.actions.structure_level_list_of_speakers.update import (
    StructureLevelListOfSpeakersUpdateAction,
)
from openslides_backend.services.database.interface import PartialModel

from ....shared.patterns import fqid_from_collection_and_id
from ...generics.update import UpdateAction
from .update import ProjectorCountdownUpdate


class CountdownCommand(Enum):
    START = auto()
    STOP = auto()
    RESET = auto()
    RESTART = auto()


class CountdownControl(UpdateAction):
    def control_countdown(
        self,
        countdown_id: int,
        command: CountdownCommand,
        default_time: int | None = None,
    ) -> None:
        countdown = self.datastore.get(
            fqid_from_collection_and_id("projector_countdown", countdown_id),
            ["countdown_time", "default_time"],
        )
        if default_time is not None:
            countdown["default_time"] = default_time

        now = round(time())
        if command == CountdownCommand.START:
            running = True
            countdown_time = countdown["countdown_time"] + now
        elif command == CountdownCommand.STOP:
            running = False
            countdown_time = countdown["countdown_time"] - now
        elif command == CountdownCommand.RESET:
            running = False
            countdown_time = countdown["default_time"]
        elif command == CountdownCommand.RESTART:
            running = True
            countdown_time = countdown["default_time"] + now
        else:
            raise NotImplementedError()

        action_data = {
            "id": countdown_id,
            "running": running,
            "countdown_time": countdown_time,
        }
        if default_time is not None:
            action_data["default_time"] = default_time
        self.execute_other_action(ProjectorCountdownUpdate, [action_data])

    def control_los_countdown(
        self,
        meeting_id: int,
        command: CountdownCommand,
        default_time: int | None = None,
    ) -> None:
        meeting = self.datastore.get(
            fqid_from_collection_and_id("meeting", meeting_id),
            ["list_of_speakers_couple_countdown", "list_of_speakers_countdown_id"],
        )
        if meeting.get("list_of_speakers_couple_countdown") and meeting.get(
            "list_of_speakers_countdown_id"
        ):
            self.control_countdown(
                meeting["list_of_speakers_countdown_id"], command, default_time
            )

    def start_structure_level_countdown(self, now: int, speaker: PartialModel) -> None:
        if (
            (level_id := speaker.get("structure_level_list_of_speakers_id"))
            and (
                speaker.get("speech_state")
                not in (
                    SpeechState.INTERPOSED_QUESTION,
                    SpeechState.INTERVENTION,
                )
            )
            and not speaker.get("point_of_order")
        ):
            self.execute_other_action(
                StructureLevelListOfSpeakersUpdateAction,
                [
                    {
                        "id": level_id,
                        "current_start_time": now,
                    }
                ],
            )

    def decrease_structure_level_countdown(
        self, now: int, speaker: PartialModel
    ) -> None:
        if (
            (level_id := speaker.get("structure_level_list_of_speakers_id"))
            and (
                speaker.get("speech_state")
                not in (
                    SpeechState.INTERPOSED_QUESTION,
                    SpeechState.INTERVENTION,
                )
            )
            and not speaker.get("point_of_order")
        ):
            # only update the level if the speaker was not paused and the speech state demands it
            start_time = cast(int, speaker.get("unpause_time", speaker["begin_time"]))
            self.execute_other_action(
                StructureLevelListOfSpeakersUpdateAction,
                [
                    {
                        "id": level_id,
                        "current_start_time": None,
                        "spoken_time": now - start_time,
                    }
                ],
            )
