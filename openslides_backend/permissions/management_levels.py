from enum import Enum
from typing import Optional

from .base_classes import VerbosePermission


class CompareRightLevel(str, VerbosePermission, Enum):
    def __new__(
        cls, value: Optional[str], weight: Optional[int] = None
    ) -> "CompareRightLevel":
        obj = str.__new__(cls, value)  # type: ignore
        obj._value_ = value
        obj.weight = weight
        return obj

    @classmethod
    def _missing_(cls, value: object) -> "CompareRightLevel":
        """
        Always return the first enum item if no matching one was found. -> NO_RIGHT must always be listed first.
        """
        return next(iter(cls))

    def check_instance(self, other: str) -> None:
        if not isinstance(other, self.__class__):
            raise TypeError(
                f"The comparison expect an {self.__class__}-type and no string!"
            )

    def __lt__(self, other: str) -> bool:
        self.check_instance(other)
        return self.weight < other.weight  # type: ignore

    def __le__(self, other: str) -> bool:
        self.check_instance(other)
        return self.weight <= other.weight  # type: ignore

    def __gt__(self, other: str) -> bool:
        self.check_instance(other)
        return self.weight > other.weight  # type: ignore

    def __ge__(self, other: str) -> bool:
        self.check_instance(other)
        return self.weight >= other.weight  # type: ignore


class OrganizationManagementLevel(CompareRightLevel):
    NO_RIGHT = ("no_right", 0)
    CAN_MANAGE_USERS = ("can_manage_users", 1)
    CAN_MANAGE_ORGANISATION = ("can_manage_organization", 2)
    SUPERADMIN = ("superadmin", 3)

    def get_base_model(self) -> str:
        return "organization"


class CommitteeManagementLevel(CompareRightLevel):
    NO_RIGHT = ("no_right", 0)
    CAN_MANAGE = ("can_manage", 1)

    def get_base_model(self) -> str:
        return "committee"
