# Code generated. DO NOT EDIT.

from typing import Dict, List

# Holds the corresponding parent for each permission.
permissions: Dict[str, List[str]] = {
    "agenda_item.can_see": ["agenda_item.can_see_internal"],
    "agenda_item.can_see_internal": ["agenda_item.can_manage"],
    "agenda_item.can_manage": [],
    "assignment.can_see": [
        "assignment.can_nominate_other",
        "assignment.can_nominate_self",
    ],
    "assignment.can_nominate_other": ["assignment.can_manage"],
    "assignment.can_manage": [],
    "assignment.can_nominate_self": [],
    "list_of_speakers.can_see": [
        "list_of_speakers.can_manage",
        "list_of_speakers.can_be_speaker",
    ],
    "list_of_speakers.can_manage": [],
    "list_of_speakers.can_be_speaker": [],
    "mediafile.can_see": ["mediafile.can_manage"],
    "mediafile.can_manage": [],
    "meeting.can_manage_settings": [],
    "meeting.can_manage_logos_and_fonts": [],
    "meeting.can_see_frontpage": [],
    "meeting.can_see_autopilot": [],
    "meeting.can_see_livestream": [],
    "meeting.can_see_history": [],
    "motion.can_see": [
        "motion.can_manage_metadata",
        "motion.can_manage_polls",
        "motion.can_see_internal",
        "motion.can_create",
        "motion.can_create_amendments",
        "motion.can_support",
    ],
    "motion.can_manage_metadata": ["motion.can_manage"],
    "motion.can_manage_polls": ["motion.can_manage"],
    "motion.can_see_internal": ["motion.can_manage"],
    "motion.can_create": ["motion.can_manage"],
    "motion.can_create_amendments": ["motion.can_manage"],
    "motion.can_manage": [],
    "motion.can_support": [],
    "poll.can_manage": [],
    "projector.can_see": ["projector.can_manage"],
    "projector.can_manage": [],
    "tag.can_manage": [],
    "user.can_see": ["user.can_see_extra_data"],
    "user.can_see_extra_data": ["user.can_manage"],
    "user.can_manage": [],
    "user.can_change_own_password": [],
}
