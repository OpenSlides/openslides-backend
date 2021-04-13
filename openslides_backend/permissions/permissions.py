# Code generated. DO NOT EDIT.

from enum import Enum
from typing import Dict, List

from .get_permission_parts import get_permission_parts


class OrganisationManagementLevel(str, Enum):
    SUPERADMIN = "superadmin"
    CAN_MANAGE_USERS = "can_manage_users"
    CAN_MANAGE_ORGANISATION = "can_manage_organisation"

    @classmethod
    def get_level_number(
        cls, oml: "OrganisationManagementLevel", default_level:int=0
    ) -> int:
        return OrganisationManagementLevel_numbers.get(oml, default_level)


OrganisationManagementLevel_numbers = {
    OrganisationManagementLevel.SUPERADMIN: 3,
    OrganisationManagementLevel.CAN_MANAGE_ORGANISATION: 2,
    OrganisationManagementLevel.CAN_MANAGE_USERS: 1,
}


class Permission(str):
    """ Marker class to use typing with permissions. """


class _AgendaItem(Permission, Enum):
    CAN_SEE_INTERNAL = "agenda_item.can_see_internal"
    CAN_SEE = "agenda_item.can_see"
    CAN_MANAGE = "agenda_item.can_manage"


class _Assignment(Permission, Enum):
    CAN_SEE = "assignment.can_see"
    CAN_NOMINATE_OTHER = "assignment.can_nominate_other"
    CAN_NOMINATE_SELF = "assignment.can_nominate_self"
    CAN_MANAGE = "assignment.can_manage"


class _ListOfSpeakers(Permission, Enum):
    CAN_SEE = "list_of_speakers.can_see"
    CAN_MANAGE = "list_of_speakers.can_manage"
    CAN_BE_SPEAKER = "list_of_speakers.can_be_speaker"


class _Mediafile(Permission, Enum):
    CAN_SEE = "mediafile.can_see"
    CAN_MANAGE = "mediafile.can_manage"


class _Meeting(Permission, Enum):
    CAN_SEE_HISTORY = "meeting.can_see_history"
    CAN_MANAGE_LOGOS_AND_FONTS = "meeting.can_manage_logos_and_fonts"
    CAN_SEE_FRONTPAGE = "meeting.can_see_frontpage"
    CAN_SEE_AUTOPILOT = "meeting.can_see_autopilot"
    CAN_MANAGE_SETTINGS = "meeting.can_manage_settings"
    CAN_SEE_LIVESTREAM = "meeting.can_see_livestream"


class _Motion(Permission, Enum):
    CAN_CREATE = "motion.can_create"
    CAN_MANAGE = "motion.can_manage"
    CAN_SUPPORT = "motion.can_support"
    CAN_MANAGE_METADATA = "motion.can_manage_metadata"
    CAN_MANAGE_POLLS = "motion.can_manage_polls"
    CAN_SEE = "motion.can_see"
    CAN_CREATE_AMENDMENTS = "motion.can_create_amendments"
    CAN_SEE_INTERNAL = "motion.can_see_internal"


class _Poll(Permission, Enum):
    CAN_MANAGE = "poll.can_manage"


class _Projector(Permission, Enum):
    CAN_MANAGE = "projector.can_manage"
    CAN_SEE = "projector.can_see"


class _Tag(Permission, Enum):
    CAN_MANAGE = "tag.can_manage"


class _User(Permission, Enum):
    CAN_SEE_EXTRA_DATA = "user.can_see_extra_data"
    CAN_MANAGE = "user.can_manage"
    CAN_CHANGE_OWN_PASSWORD = "user.can_change_own_password"
    CAN_SEE = "user.can_see"


class Permissions:
    @classmethod
    def parse(cls, permission: str) -> Permission:
        parts = get_permission_parts(permission)
        PermissionClass = getattr(cls, parts[0])
        return getattr(PermissionClass, parts[1])

    AgendaItem = _AgendaItem
    Assignment = _Assignment
    ListOfSpeakers = _ListOfSpeakers
    Mediafile = _Mediafile
    Meeting = _Meeting
    Motion = _Motion
    Poll = _Poll
    Projector = _Projector
    Tag = _Tag
    User = _User


# Holds the corresponding parent for each permission.
permission_parents: Dict[Permission, List[Permission]] = {
    _AgendaItem.CAN_SEE: [_AgendaItem.CAN_SEE_INTERNAL],
    _AgendaItem.CAN_SEE_INTERNAL: [_AgendaItem.CAN_MANAGE],
    _AgendaItem.CAN_MANAGE: [],
    _Assignment.CAN_SEE: [
        _Assignment.CAN_NOMINATE_OTHER,
        _Assignment.CAN_NOMINATE_SELF,
    ],
    _Assignment.CAN_NOMINATE_OTHER: [_Assignment.CAN_MANAGE],
    _Assignment.CAN_MANAGE: [],
    _Assignment.CAN_NOMINATE_SELF: [],
    _ListOfSpeakers.CAN_SEE: [
        _ListOfSpeakers.CAN_MANAGE,
        _ListOfSpeakers.CAN_BE_SPEAKER,
    ],
    _ListOfSpeakers.CAN_MANAGE: [],
    _ListOfSpeakers.CAN_BE_SPEAKER: [],
    _Mediafile.CAN_SEE: [_Mediafile.CAN_MANAGE],
    _Mediafile.CAN_MANAGE: [],
    _Meeting.CAN_MANAGE_SETTINGS: [],
    _Meeting.CAN_MANAGE_LOGOS_AND_FONTS: [],
    _Meeting.CAN_SEE_FRONTPAGE: [],
    _Meeting.CAN_SEE_AUTOPILOT: [],
    _Meeting.CAN_SEE_LIVESTREAM: [],
    _Meeting.CAN_SEE_HISTORY: [],
    _Motion.CAN_SEE: [
        _Motion.CAN_MANAGE_METADATA,
        _Motion.CAN_MANAGE_POLLS,
        _Motion.CAN_SEE_INTERNAL,
        _Motion.CAN_CREATE,
        _Motion.CAN_CREATE_AMENDMENTS,
        _Motion.CAN_SUPPORT,
    ],
    _Motion.CAN_MANAGE_METADATA: [_Motion.CAN_MANAGE],
    _Motion.CAN_MANAGE_POLLS: [_Motion.CAN_MANAGE],
    _Motion.CAN_SEE_INTERNAL: [_Motion.CAN_MANAGE],
    _Motion.CAN_CREATE: [_Motion.CAN_MANAGE],
    _Motion.CAN_CREATE_AMENDMENTS: [_Motion.CAN_MANAGE],
    _Motion.CAN_MANAGE: [],
    _Motion.CAN_SUPPORT: [],
    _Poll.CAN_MANAGE: [],
    _Projector.CAN_SEE: [_Projector.CAN_MANAGE],
    _Projector.CAN_MANAGE: [],
    _Tag.CAN_MANAGE: [],
    _User.CAN_SEE: [_User.CAN_SEE_EXTRA_DATA],
    _User.CAN_SEE_EXTRA_DATA: [_User.CAN_MANAGE],
    _User.CAN_MANAGE: [],
    _User.CAN_CHANGE_OWN_PASSWORD: [],
}
