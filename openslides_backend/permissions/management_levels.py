from enum import Enum
from typing import cast

from .base_classes import VerbosePermission


class CompareRightLevel(str, VerbosePermission, Enum):
    @classmethod
    def _missing_(cls, _: object) -> "CompareRightLevel":
        """
        Always return the first enum item if no matching one was found. -> NO_RIGHT must always be listed first.
        """
        return cls(list(cls)[0])

    def check_instance(self, other: str) -> "CompareRightLevel":
        """
        Check that only objects of the same class are compared with each other and cast it
        accordingly. (Supertype `str` enforces that the initial argument type is also `str`)
        """
        if not isinstance(other, type(self)):
            raise TypeError(
                f"The comparison expect an {type(self)}-type and no string!"
            )
        return cast("CompareRightLevel", other)

    @property
    def weight(self) -> int:
        return list(type(self)).index(self)

    def __lt__(self, other: str) -> bool:
        other = self.check_instance(other)
        return self.weight < other.weight

    def __le__(self, other: str) -> bool:
        other = self.check_instance(other)
        return self.weight <= other.weight

    def __gt__(self, other: str) -> bool:
        return not self <= other

    def __ge__(self, other: str) -> bool:
        return not self < other


class OrganizationManagementLevel(CompareRightLevel):
    NO_RIGHT = "no_right"
    CAN_MANAGE_USERS = "can_manage_users"
    CAN_MANAGE_ORGANIZATION = "can_manage_organization"
    SUPERADMIN = "superadmin"

    def get_base_model(self) -> str:
        return "organization"


class CommitteeManagementLevel(CompareRightLevel):
    NO_RIGHT = "no_right"
    CAN_MANAGE = "can_manage"

    def get_base_model(self) -> str:
        return "committee"

class SystemManagementLevel:

    def __init__(self, permission: str):
        self.permission = permission