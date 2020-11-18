from typing import Dict, Type

from .base import Action


def prepare_actions_map() -> None:
    """
    This function just imports all action modules so that the actions are
    recognized by the system and the register decorator can do its work.

    New modules have to be added here.
    """
    from . import (  # noqa
        agenda_item,
        assignment,
        assignment_candidate,
        assignment_option,
        assignment_poll,
        assignment_vote,
        committee,
        group,
        list_of_speakers,
        mediafile,
        meeting,
        motion,
        motion_block,
        motion_category,
        motion_change_recommendation,
        motion_comment,
        motion_comment_section,
        motion_option,
        motion_poll,
        motion_state,
        motion_statute_paragraph,
        motion_submitter,
        motion_vote,
        motion_workflow,
        personal_note,
        speaker,
        tag,
        topic,
        user,
    )


actions_map: Dict[str, Type[Action]] = {}


prepare_actions_map()
