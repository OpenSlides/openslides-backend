from tests.system.migrations.conftest import DoesNotExist


def test_migration(write, finalize, assert_model, read_model):
    """
    ids for collections:
     1x meeting_user (will be created)
     2x committee
     3x mediafile
     4x meeting
     5x group
     6x motion
     7x projector
     8x poll
     9x option
    10x vote
    11x personal_note
    12x speaker
    13x assignment_candidate
    14x motion_submitter
    15x chat_message
    16x motion_state
    17x list_of_speakers
    18x assignment
    19x chat_group
    20x theme
    21x motion_workflow
    22x user
    """
    write(
        # motions
        {
            "type": "create",
            "fqid": "motion/61",
            "fields": {
                "id": 61,
                "amendment_paragraph_$": ["0", "1", "2", "42"],
                "amendment_paragraph_$0": "change",
                "amendment_paragraph_$1": "change",
                "amendment_paragraph_$2": "change",
                "amendment_paragraph_$42": "change",
            },
        },
    )
    finalize("0045_fix_amendment_paragraph")

    assert_model(
        "motion/61",
        {
            "id": 61,
            "amendment_paragraphs": {
                "0": "change",
                "1": "change",
                "2": "change",
                "42": "change",
            },
        },
    )
