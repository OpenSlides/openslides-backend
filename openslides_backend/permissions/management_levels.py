from enum import Enum


class CompareRightLevel(str, Enum):
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


class CommitteeManagementLevel(CompareRightLevel):
    """ 2nd Permission Type, implemented as User.committee_as_manager_ids """

    MANAGER = ("can_manage", 1)
    NO_RIGHT = ("no_right", 0)
