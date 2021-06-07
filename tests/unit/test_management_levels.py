import pytest

from openslides_backend.permissions.management_levels import (
    CommitteeManagementLevel,
    OrganizationManagementLevel,
)


def test_orgamanagement_level_lt() -> None:
    assert (
        OrganizationManagementLevel.CAN_MANAGE_USERS
        < OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    )


def test_orgamanagement_level_le() -> None:
    assert (
        OrganizationManagementLevel.CAN_MANAGE_USERS
        <= OrganizationManagementLevel.CAN_MANAGE_USERS
    )


def test_orgamanagement_level_gt() -> None:
    assert (
        OrganizationManagementLevel.SUPERADMIN
        > OrganizationManagementLevel.CAN_MANAGE_ORGANIZATION
    )


def test_orgamanagement_level_ge() -> None:
    assert (
        OrganizationManagementLevel.SUPERADMIN >= OrganizationManagementLevel.SUPERADMIN
    )


def test_committee_level_le() -> None:
    assert CommitteeManagementLevel.CAN_MANAGE <= CommitteeManagementLevel.CAN_MANAGE


def test_committee_level_gt() -> None:
    assert not CommitteeManagementLevel.CAN_MANAGE > CommitteeManagementLevel.CAN_MANAGE


def test_committee_level_ge() -> None:
    assert CommitteeManagementLevel.CAN_MANAGE >= CommitteeManagementLevel.CAN_MANAGE


def test_committee_level_string_CML() -> None:
    with pytest.raises(TypeError) as exc:
        "A" < CommitteeManagementLevel.CAN_MANAGE
    assert (
        "The comparison expect an <enum 'CommitteeManagementLevel'>-type and no string!"
        in str(exc.value)
    )


def test_committee_level_CML_string() -> None:
    with pytest.raises(TypeError) as exc:
        CommitteeManagementLevel.CAN_MANAGE > "A"
    assert (
        "The comparison expect an <enum 'CommitteeManagementLevel'>-type and no string!"
        in str(exc.value)
    )


def test_implicit_no_right_1() -> None:
    assert OrganizationManagementLevel(None) == OrganizationManagementLevel.NO_RIGHT


def test_implicit_no_right_2() -> None:
    assert OrganizationManagementLevel("") == OrganizationManagementLevel.NO_RIGHT
