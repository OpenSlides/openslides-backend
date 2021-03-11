from openslides_backend.permissions.permission_helper import is_child_permission


def test_is_child_permission_equal() -> None:
    assert is_child_permission("agenda_item.can_manage", "agenda_item.can_manage")


def test_is_child_permission_child() -> None:
    assert is_child_permission("agenda_item.can_see", "agenda_item.can_manage")


def test_is_child_permission_multipath_1() -> None:
    assert is_child_permission(
        "list_of_speakers.can_see", "list_of_speakers.can_manage"
    )


def test_is_child_permission_multipath_2() -> None:
    assert is_child_permission(
        "list_of_speakers.can_see", "list_of_speakers.can_be_speaker"
    )


def test_is_child_permission_multipath_3() -> None:
    assert is_child_permission("motion.can_see", "motion.can_manage")


def test_is_child_permission_parent() -> None:
    assert not is_child_permission("agenda_item.can_manage", "agenda_item.can_see")


def test_is_child_permission_different_collections() -> None:
    assert not is_child_permission("agenda_item.can_see", "motion.can_manage")
