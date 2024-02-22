import pytest

from openslides_backend.action.actions.motion.mixins import TextHashMixin


def create_motion(id, meeting_id, text=None, paragraphs=None, lead_motion_id=None):
    return {
        "type": "create",
        "fqid": f"motion/{id}",
        "fields": {
            "id": id,
            "meeting_id": meeting_id,
            "lead_motion_id": lead_motion_id,
            "text": text,
            "amendment_paragraphs": paragraphs,
        },
    }


@pytest.fixture()
def assert_motion(assert_model):
    def _assert_motion(motion, identical_motion_ids):
        expected = {
            **motion,
            "text_hash": TextHashMixin.get_hash_for_motion(motion),
            "identical_motion_ids": identical_motion_ids,
        }
        assert_model(f"motion/{motion['id']}", expected)

    yield _assert_motion


def test_migration(write, finalize, assert_motion):
    write(
        {
            "type": "create",
            "fqid": "meeting/1",
            "fields": {
                "id": 1,
                "motion_ids": [1, 2, 3, 4, 5, 6, 11, 12, 42],
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
                "amendment_ids": [4, 5, 6, 11, 12],
            },
        },
        create_motion(4, 1, "text1", lead_motion_id=42),
        create_motion(5, 1, "text1", lead_motion_id=42),
        create_motion(6, 1, "text2", lead_motion_id=42),
        create_motion(11, 1, paragraphs={"0": "<p>text</p>"}, lead_motion_id=42),
        create_motion(12, 1, paragraphs={"0": "<div>text</div>"}, lead_motion_id=42),
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

    assert_motion({"id": 1, "meeting_id": 1, "text": "text1"}, [2])
    assert_motion({"id": 2, "meeting_id": 1, "text": "text1"}, [1])
    assert_motion({"id": 3, "meeting_id": 1, "text": "text2"}, [])
    assert_motion(
        {"id": 4, "meeting_id": 1, "text": "text1", "lead_motion_id": 42}, [5]
    )
    assert_motion(
        {"id": 5, "meeting_id": 1, "text": "text1", "lead_motion_id": 42}, [4]
    )
    assert_motion({"id": 6, "meeting_id": 1, "text": "text2", "lead_motion_id": 42}, [])
    assert_motion(
        {
            "id": 11,
            "meeting_id": 1,
            "amendment_paragraphs": {"0": "<p>text</p>"},
            "lead_motion_id": 42,
        },
        [12],
    )
    assert_motion(
        {
            "id": 12,
            "meeting_id": 1,
            "amendment_paragraphs": {"0": "<div>text</div>"},
            "lead_motion_id": 42,
        },
        [11],
    )
    assert_motion({"id": 7, "meeting_id": 2, "text": "text1"}, [8, 9])
    assert_motion({"id": 8, "meeting_id": 2, "text": "text1"}, [7, 9])
    assert_motion({"id": 9, "meeting_id": 2, "text": "text1"}, [7, 8])
