

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
        {
            "type": "create",
            "fqid": "motion/23880",
            "fields": {
                "id": 23880,
                "title": "Änderungsantrag zu 01",
                "reason": "",
                "created": 1678286817,
                "state_id": 3564,
                "meeting_id": 177,
                "sort_weight": 10000,
                "last_modified": 1678286817,
                "meta_position": 13607,
                "submitter_ids": [25353],
                "lead_motion_id": 23879,
                "category_weight": 10000,
                "sequential_number": 2,
                "start_line_number": 1,
                "workflow_timestamp": 1678286817,
                "list_of_speakers_id": 25721,
                "amendment_paragraph_$": ["0"],
                "amendment_paragraph_$0": "<p>Dieser Test Antrag soll weitergeleitet werden. Und dann dazu ein &Auml;nderungsantrag gestellt werden.</p>",
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
    assert_model(
        "motion/23880",
        {
            "id": 23880,
            "title": "Änderungsantrag zu 01",
            "reason": "",
            "created": 1678286817,
            "state_id": 3564,
            "meeting_id": 177,
            "sort_weight": 10000,
            "last_modified": 1678286817,
            "meta_position": 13607,
            "submitter_ids": [25353],
            "lead_motion_id": 23879,
            "category_weight": 10000,
            "sequential_number": 2,
            "start_line_number": 1,
            "workflow_timestamp": 1678286817,
            "list_of_speakers_id": 25721,
            "amendment_paragraphs": "<p>Dieser Test Antrag soll weitergeleitet werden. Und dann dazu ein &Auml;nderungsantrag gestellt werden.</p>",
        },
    )
