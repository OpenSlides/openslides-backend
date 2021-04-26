import pytest

from openslides_backend.permissions.permissions import (
    CommitteeManagementLevel,
    OrganisationManagementLevel,
)
from openslides_backend.shared.exceptions import PermissionException


def test_orgamanagement_level_lt() -> None:
    assert (
        OrganisationManagementLevel.CAN_MANAGE_USERS
        < OrganisationManagementLevel.CAN_MANAGE_ORGANISATION
    )


def test_orgamanagement_level_le() -> None:
    assert (
        OrganisationManagementLevel.CAN_MANAGE_USERS
        <= OrganisationManagementLevel.CAN_MANAGE_USERS
    )


def test_orgamanagement_level_gt() -> None:
    assert (
        OrganisationManagementLevel.SUPERADMIN
        > OrganisationManagementLevel.CAN_MANAGE_ORGANISATION
    )


def test_orgamanagement_level_ge() -> None:
    assert (
        OrganisationManagementLevel.SUPERADMIN >= OrganisationManagementLevel.SUPERADMIN
    )


def test_committee_level_le() -> None:
    assert CommitteeManagementLevel.MANAGER <= CommitteeManagementLevel.MANAGER


def test_committee_level_gt() -> None:
    # with pytest.raises(AssertionError) as excinfo:
    assert not CommitteeManagementLevel.MANAGER > CommitteeManagementLevel.MANAGER
    # assert "xxxxx" in str(excinfo.value)


def test_committee_level_ge() -> None:
    assert CommitteeManagementLevel.MANAGER >= CommitteeManagementLevel.MANAGER


def test_committee_level_string_CML() -> None:
    with pytest.raises(PermissionException) as exc:
        "A" < CommitteeManagementLevel.MANAGER
    assert (
        "The comparison expect an <enum 'CommitteeManagementLevel'>-type and no string!"
        in str(exc.value)
    )


def test_committee_level_CML_string() -> None:
    with pytest.raises(PermissionException) as exc:
        CommitteeManagementLevel.MANAGER > "A"
    assert (
        "The comparison expect an <enum 'CommitteeManagementLevel'>-type and no string!"
        in str(exc.value)
    )
