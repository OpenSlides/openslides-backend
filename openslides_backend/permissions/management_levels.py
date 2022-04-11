from enum import Enum
from typing import cast

from .base_classes import VerbosePermission


class CompareRightLevel(str, VerbosePermission, Enum):
    @classmethod
    def _missing_(cls, value: object) -> "CompareRightLevel":
        """
        Always return the first enum item if no matching one was found. -> NO_RIGHT must always be listed first.
        """
        return list(cls)[0]

    def check_instance(self, other: str) -> "CompareRightLevel":
        """
        Check that only objects of the same class are compared with each other and cast it
        accordingly. (Supertype `str` enforces that the initial argument type is also `str`)
        """
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"The comparison expect an {self.__class__}-type and no string!"
            )
        return cast("CompareRightLevel", other)

    @property
    def weight(self) -> int:
        # mypy can't infer the correct list type here
        # may be related to https://github.com/python/mypy/issues/11784
        return list(self.__class__).index(self)  # type: ignore

    def __lt__(self, other: str) -> bool:
        other = self.check_instance(other)
        return self.weight < other.weight

    def __le__(self, other: str) -> bool:
        other = self.check_instance(other)
        return self.weight <= other.weight

    def __gt__(self, other: str) -> bool:
        other = self.check_instance(other)
        return self.weight > other.weight

    def __ge__(self, other: str) -> bool:
        other = self.check_instance(other)
        return self.weight >= other.weight


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
