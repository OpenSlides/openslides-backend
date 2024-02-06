# Code generated. DO NOT EDIT.

from enum import Enum

from .base_classes import Permission

PERMISSION_YML_CHECKSUM = "ae5496b33e65c38123eac203af69434b"


class _AgendaItem(str, Permission, Enum):
    CAN_MANAGE = "agenda_item.can_manage"
    CAN_SEE = "agenda_item.can_see"
    CAN_SEE_INTERNAL = "agenda_item.can_see_internal"


class _Assignment(str, Permission, Enum):
    CAN_MANAGE = "assignment.can_manage"
    CAN_NOMINATE_OTHER = "assignment.can_nominate_other"
    CAN_NOMINATE_SELF = "assignment.can_nominate_self"
    CAN_SEE = "assignment.can_see"


class _Chat(str, Permission, Enum):
    CAN_MANAGE = "chat.can_manage"


class _ListOfSpeakers(str, Permission, Enum):
    CAN_BE_SPEAKER = "list_of_speakers.can_be_speaker"
    CAN_MANAGE = "list_of_speakers.can_manage"
    CAN_SEE = "list_of_speakers.can_see"


class _Mediafile(str, Permission, Enum):
    CAN_MANAGE = "mediafile.can_manage"
    CAN_SEE = "mediafile.can_see"


class _Meeting(str, Permission, Enum):
    CAN_MANAGE_LOGOS_AND_FONTS = "meeting.can_manage_logos_and_fonts"
    CAN_MANAGE_SETTINGS = "meeting.can_manage_settings"
    CAN_SEE_AUTOPILOT = "meeting.can_see_autopilot"
    CAN_SEE_FRONTPAGE = "meeting.can_see_frontpage"
    CAN_SEE_HISTORY = "meeting.can_see_history"
    CAN_SEE_LIVESTREAM = "meeting.can_see_livestream"


class _Motion(str, Permission, Enum):
    CAN_CREATE = "motion.can_create"
    CAN_CREATE_AMENDMENTS = "motion.can_create_amendments"
    CAN_FORWARD = "motion.can_forward"
    CAN_MANAGE = "motion.can_manage"
    CAN_MANAGE_METADATA = "motion.can_manage_metadata"
    CAN_MANAGE_POLLS = "motion.can_manage_polls"
    CAN_SEE = "motion.can_see"
    CAN_SEE_INTERNAL = "motion.can_see_internal"
    CAN_SUPPORT = "motion.can_support"


class _Poll(str, Permission, Enum):
    CAN_MANAGE = "poll.can_manage"


class _Projector(str, Permission, Enum):
    CAN_MANAGE = "projector.can_manage"
    CAN_SEE = "projector.can_see"


class _Tag(str, Permission, Enum):
    CAN_MANAGE = "tag.can_manage"


class _User(str, Permission, Enum):
    CAN_MANAGE = "user.can_manage"
    CAN_MANAGE_PRESENCE = "user.can_manage_presence"
    CAN_SEE = "user.can_see"
    CAN_SEE_PERSONAL_DATA = "user.can_see_personal_data"
    CAN_UPDATE = "user.can_update"


class Permissions:
    AgendaItem = _AgendaItem
    Assignment = _Assignment
    Chat = _Chat
    ListOfSpeakers = _ListOfSpeakers
    Mediafile = _Mediafile
    Meeting = _Meeting
    Motion = _Motion
    Poll = _Poll
    Projector = _Projector
    Tag = _Tag
    User = _User


# Holds the corresponding parent for each permission.
permission_parents: dict[Permission, list[Permission]] = {
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
    _Chat.CAN_MANAGE: [],
    _ListOfSpeakers.CAN_SEE: [_ListOfSpeakers.CAN_MANAGE],
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
        _Motion.CAN_FORWARD,
        _Motion.CAN_SUPPORT,
    ],
    _Motion.CAN_MANAGE_METADATA: [_Motion.CAN_MANAGE],
    _Motion.CAN_MANAGE_POLLS: [_Motion.CAN_MANAGE],
    _Motion.CAN_SEE_INTERNAL: [_Motion.CAN_MANAGE],
    _Motion.CAN_CREATE: [_Motion.CAN_MANAGE],
    _Motion.CAN_CREATE_AMENDMENTS: [_Motion.CAN_MANAGE],
    _Motion.CAN_FORWARD: [_Motion.CAN_MANAGE],
    _Motion.CAN_MANAGE: [],
    _Motion.CAN_SUPPORT: [],
    _Poll.CAN_MANAGE: [],
    _Projector.CAN_SEE: [_Projector.CAN_MANAGE],
    _Projector.CAN_MANAGE: [],
    _Tag.CAN_MANAGE: [],
    _User.CAN_SEE: [_User.CAN_MANAGE_PRESENCE, _User.CAN_SEE_PERSONAL_DATA],
    _User.CAN_MANAGE_PRESENCE: [_User.CAN_MANAGE],
    _User.CAN_SEE_PERSONAL_DATA: [_User.CAN_UPDATE],
    _User.CAN_UPDATE: [_User.CAN_MANAGE],
    _User.CAN_MANAGE: [],
}
