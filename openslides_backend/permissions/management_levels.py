from enum import Enum

from .base_classes import VerbosePermission


class CompareRightLevel(str, VerbosePermission, Enum):
    def __new__(cls, value: str, weight: int):  # type: ignore
        obj = str.__new__(cls, value)  # type: ignore
        obj._value_ = value
        obj.weight = weight
        return obj

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


class OrganisationManagementLevel(CompareRightLevel):
    SUPERADMIN = ("superadmin", 3)
    CAN_MANAGE_USERS = ("can_manage_users", 1)
    CAN_MANAGE_ORGANISATION = ("can_manage_organisation", 2)
    NO_RIGHT = ("no_right", 0)

    def get_base_model(self) -> str:
        return "organisation"


class CommitteeManagementLevel(CompareRightLevel):
    CAN_MANAGE = ("can_manage", 1)
    NO_RIGHT = ("no_right", 0)

    def get_base_model(self) -> str:
        return "committee"
