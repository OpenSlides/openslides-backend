import pytest

from openslides_backend.action.actions.motion.mixins import TextHashMixin


def create_motion(id, meeting_id, text, lead_motion_id=None):
    return {
        "type": "create",
        "fqid": f"motion/{id}",
        "fields": {
            "id": id,
            "meeting_id": meeting_id,
            "lead_motion_id": lead_motion_id,
            "text": text,
        },
    }


@pytest.fixture()
def assert_motion(assert_model):
    def _assert_motion(id, meeting_id, text, identical_motion_ids, lead_motion_id=None):
        expected = {
            "id": id,
            "meeting_id": meeting_id,
            "text": text,
            "text_hash": TextHashMixin.get_hash(text),
            "identical_motion_ids": identical_motion_ids,
        }
        if lead_motion_id is not None:
            expected["lead_motion_id"] = lead_motion_id
        assert_model(f"motion/{id}", expected)

    yield _assert_motion


def test_migration(write, finalize, assert_motion):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {
                "id": 1,
                "motion_ids": [1, 2, 3, 4, 5, 6, 42],
            },
        },
        create_motion(1, 1, "text1"),
        create_motion(2, 1, "text1"),
        create_motion(3, 1, "text2"),
        {
            "type": "create",
            "fqid": "motion/42",
            "fields": {
                "id": 42,
                "meeting_id": 1,
                "amendment_ids": [4, 5, 6],
            },
        },
        create_motion(4, 1, "text1", 42),
        create_motion(5, 1, "text1", 42),
        create_motion(6, 1, "text2", 42),
        {
            "type": "create",
            "fqid": "meeting/2",
            "fields": {
                "id": 2,
                "motion_ids": [7, 8, 9],
            },
        },
        create_motion(7, 2, "text1"),
        create_motion(8, 2, "text1"),
        create_motion(9, 2, "text1"),
    )
    finalize("0050_add_identical_motions")

    assert_motion(1, 1, "text1", [2])
    assert_motion(2, 1, "text1", [1])
    assert_motion(3, 1, "text2", [])
    assert_motion(4, 1, "text1", [5], 42)
    assert_motion(5, 1, "text1", [4], 42)
    assert_motion(6, 1, "text2", [], 42)
    assert_motion(7, 2, "text1", [8, 9])
    assert_motion(8, 2, "text1", [7, 9])
    assert_motion(9, 2, "text1", [7, 8])
