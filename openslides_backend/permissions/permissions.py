# Code generated. DO NOT EDIT.

from enum import Enum
from typing import Dict, List

from ..shared.exceptions import PermissionException
from .get_permission_parts import get_permission_parts


class CompareRightLevel(str):
    def get_number(self, value) -> int:  # type: ignore
        return 0

    def __lt__(self, other: str) -> bool:
        self_number = self.get_number(self)
        other_number = self.get_number(other)
        return self_number < other_number

    def __le__(self, other: str) -> bool:
        self_number = self.get_number(self)
        other_number = self.get_number(other)
        return self_number <= other_number

    def __gt__(self, other: str) -> bool:
        self_number = self.get_number(self)
        other_number = self.get_number(other)
        return self_number > other_number

    def __ge__(self, other: str) -> bool:
        self_number = self.get_number(self)
        other_number = self.get_number(other)
        return self_number >= other_number


class OrganisationManagementLevel(CompareRightLevel, Enum):
    SUPERADMIN = "superadmin"
    CAN_MANAGE_USERS = "can_manage_users"
    CAN_MANAGE_ORGANISATION = "can_manage_organisation"
    NO_RIGHT = "no_right"

    def get_number(self, value: "OrganisationManagementLevel") -> int:
        if not isinstance(value, self.__class__):
            raise PermissionException(
                f"The comparison expect an {self.__class__}-type and no string!"
            )
        numbers = {
            "superadmin": 3,
            "can_manage_organisation": 2,
            "can_manage_users": 1,
            "no_right": 0,
        }
        return numbers.get(value, 0)


class CommitteeManagementLevel(CompareRightLevel, Enum):
    """ 2nd Permission Type, implemented as User.committee_as_manager_ids """

    MANAGER = "can_manage"
    NO_RIGHT = "no_right"

    def get_number(self, value: "CommitteeManagementLevel") -> int:
        if not isinstance(value, self.__class__):
            raise PermissionException(
                f"The comparison expect an {self.__class__}-type and no string!"
            )
        numbers = {
            "can_manage": 1,
            "no_right": 0,
        }
        return numbers.get(value, 0)


class Permission(str):
    """ Marker class to use typing with permissions. """

    def __str__(self) -> str:
        return self.value  # type: ignore


class _AgendaItem(Permission, Enum):
    CAN_MANAGE = "agenda_item.can_manage"
    CAN_SEE = "agenda_item.can_see"
    CAN_SEE_INTERNAL = "agenda_item.can_see_internal"


class _Assignment(Permission, Enum):
    CAN_MANAGE = "assignment.can_manage"
    CAN_NOMINATE_OTHER = "assignment.can_nominate_other"
    CAN_NOMINATE_SELF = "assignment.can_nominate_self"
    CAN_SEE = "assignment.can_see"


class _ListOfSpeakers(Permission, Enum):
    CAN_BE_SPEAKER = "list_of_speakers.can_be_speaker"
    CAN_MANAGE = "list_of_speakers.can_manage"
    CAN_SEE = "list_of_speakers.can_see"


class _Mediafile(Permission, Enum):
    CAN_MANAGE = "mediafile.can_manage"
    CAN_SEE = "mediafile.can_see"


class _Meeting(Permission, Enum):
    CAN_MANAGE_LOGOS_AND_FONTS = "meeting.can_manage_logos_and_fonts"
    CAN_MANAGE_SETTINGS = "meeting.can_manage_settings"
    CAN_SEE_AUTOPILOT = "meeting.can_see_autopilot"
    CAN_SEE_FRONTPAGE = "meeting.can_see_frontpage"
    CAN_SEE_HISTORY = "meeting.can_see_history"
    CAN_SEE_LIVESTREAM = "meeting.can_see_livestream"


class _Motion(Permission, Enum):
    CAN_CREATE = "motion.can_create"
    CAN_CREATE_AMENDMENTS = "motion.can_create_amendments"
    CAN_MANAGE = "motion.can_manage"
    CAN_MANAGE_METADATA = "motion.can_manage_metadata"
    CAN_MANAGE_POLLS = "motion.can_manage_polls"
    CAN_SEE = "motion.can_see"
    CAN_SEE_INTERNAL = "motion.can_see_internal"
    CAN_SUPPORT = "motion.can_support"


class _Poll(Permission, Enum):
    CAN_MANAGE = "poll.can_manage"


class _Projector(Permission, Enum):
    CAN_MANAGE = "projector.can_manage"
    CAN_SEE = "projector.can_see"


class _Tag(Permission, Enum):
    CAN_MANAGE = "tag.can_manage"


class _User(Permission, Enum):
    CAN_CHANGE_OWN_PASSWORD = "user.can_change_own_password"
    CAN_MANAGE = "user.can_manage"
    CAN_SEE = "user.can_see"
    CAN_SEE_EXTRA_DATA = "user.can_see_extra_data"


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
