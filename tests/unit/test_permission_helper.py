from openslides_backend.permissions.permission_helper import is_child_permission
from openslides_backend.permissions.permissions import Permissions


def test_is_child_permission_equal() -> None:
    assert is_child_permission(
        Permissions.AgendaItem.CAN_MANAGE, Permissions.AgendaItem.CAN_MANAGE
    )


def test_is_child_permission_child() -> None:
    assert is_child_permission(
        Permissions.AgendaItem.CAN_SEE, Permissions.AgendaItem.CAN_MANAGE
    )


def test_is_child_permission_multipath_1() -> None:
    assert is_child_permission(
        Permissions.ListOfSpeakers.CAN_SEE, Permissions.ListOfSpeakers.CAN_MANAGE
    )


def test_is_child_permission_multipath_2() -> None:
    assert not is_child_permission(
        Permissions.ListOfSpeakers.CAN_SEE, Permissions.ListOfSpeakers.CAN_BE_SPEAKER
    )


def test_is_child_permission_multipath_3() -> None:
    assert is_child_permission(
        Permissions.Motion.CAN_SEE, Permissions.Motion.CAN_MANAGE
    )


def test_is_child_permission_parent() -> None:
    assert not is_child_permission(
        Permissions.AgendaItem.CAN_MANAGE, Permissions.AgendaItem.CAN_SEE
    )


def test_is_child_permission_different_collections() -> None:
    assert not is_child_permission(
        Permissions.AgendaItem.CAN_SEE, Permissions.Motion.CAN_MANAGE
    )
