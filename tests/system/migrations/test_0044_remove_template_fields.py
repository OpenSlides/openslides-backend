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
        # organization
        {
            "type": "create",
            "fqid": "organization/1",
            "fields": {
                "id": 1,
                "default_language": "en",
                "theme_id": 201,
                "theme_ids": [201],
                "user_ids": [221, 222, 223, 224],
                "committee_ids": [11, 12],
                "active_meeting_ids": [41, 42],
            },
        },
        # theme
        {
            "type": "create",
            "fqid": "theme/201",
            "fields": {
                "id": 201,
                "name": "theme",
                "accent_500": "#000000",
                "primary_500": "#000000",
                "warn_500": "#000000",
                "theme_for_organization_id": 1,
                "organization_id": 1,
            },
        },
        # users
        {
            "type": "create",
            "fqid": "user/221",
            "fields": {
                "id": 221,
                "organization_id": 1,
                "username": "user1",
                "committee_$_management_level": ["can_manage"],
                "committee_$can_manage_management_level": [11],
                "poll_voted_$_ids": ["41", "42"],
                "poll_voted_$41_ids": [81],
                "poll_voted_$42_ids": [82],
                "option_$_ids": ["41", "42"],
                "option_$41_ids": [91, 92],
                "option_$42_ids": None,
                "vote_$_ids": ["41", "42"],
                "vote_$41_ids": [101],
                "vote_delegated_vote_$_ids": ["41", "42"],
                "vote_delegated_vote_$41_ids": [101],
                "vote_delegated_vote_$42_ids": [],
                "comment_$": ["41"],
                "comment_$41": "comment",
                "number_$": ["41"],
                "number_$41": "number",
                "structure_level_$": ["41"],
                "structure_level_$41": "structure level",
                "about_me_$": ["41"],
                "about_me_$41": "about me",
                "vote_weight_$": ["41"],
                "vote_weight_$41": "1.234567",
                "group_$_ids": ["41", "42"],
                "group_$41_ids": [51, 52],
                "group_$42_ids": [53],
                "speaker_$_ids": ["41"],
                "speaker_$41_ids": [121],
                "personal_note_$_ids": ["41"],
                "personal_note_$41_ids": [111],
                "supported_motion_$_ids": ["41"],
                "supported_motion_$41_ids": [61],
                "submitted_motion_$_ids": ["41"],
                "submitted_motion_$41_ids": [141],
                "assignment_candidate_$_ids": ["41"],
                "assignment_candidate_$41_ids": [131],
                "vote_delegated_$_to_id": ["41"],
                "vote_delegated_$41_to_id": 222,
                "chat_message_$_ids": ["41"],
                "chat_message_$41_ids": [151],
            },
        },
        {
            "type": "create",
            "fqid": "user/222",
            "fields": {
                "id": 222,
                "organization_id": 1,
                "username": "user2",
                "comment_$": [],
                "number_$": None,
                "group_$_ids": ["41"],
                "group_$41_ids": [51],
                "vote_delegations_$_from_ids": ["41"],
                "vote_delegations_$41_from_ids": [221],
            },
        },
        # users in deleted meeting
        {
            "type": "create",
            "fqid": "user/223",
            "fields": {
                "id": 223,
                "organization_id": 1,
                "username": "user3",
                "comment_$": ["43"],
                "comment_$43": "comment",
                "poll_voted_$_ids": ["43"],
                "poll_voted_$43_ids": [],
                "vote_delegated_$_to_id": ["43"],
                "vote_delegated_$43_to_id": 224,
            },
        },
        {
            "type": "create",
            "fqid": "user/224",
            "fields": {
                "id": 224,
                "organization_id": 1,
                "username": "user4",
                "vote_delegations_$_from_ids": ["43"],
                "vote_delegations_$43_from_ids": [223],
            },
        },
        # committees
        # with correct replacements
        {
            "type": "create",
            "fqid": "committee/11",
            "fields": {
                "id": 11,
                "organization_id": 1,
                "name": "committee1",
                "user_$_management_level": ["can_manage"],
                "user_$can_manage_management_level": [221],
                "meeting_ids": [41],
            },
        },
        # with missing replacement - structured field will be silently kept
        {
            "type": "create",
            "fqid": "committee/12",
            "fields": {
                "id": 12,
                "organization_id": 1,
                "name": "committee2",
                "user_$_management_level": [],
                "user_$can_manage_management_level": [221],
                "meeting_ids": [42],
            },
        },
        # meetings
        {
            "type": "create",
            "fqid": "meeting/41",
            "fields": {
                "id": 41,
                "is_active_in_organization_id": 1,
                "committee_id": 11,
                "motion_ids": [61],
                "mediafile_ids": [31, 32],
                "projector_ids": [71, 72],
                "group_ids": [51, 52],
                "poll_ids": [81],
                "option_ids": [91, 92],
                "vote_ids": [101],
                "speaker_ids": [121],
                "list_of_speakers_ids": [171, 172],
                "personal_note_ids": [111],
                "motion_submitter_ids": [141],
                "motion_workflow_ids": [211],
                "motion_state_ids": [161],
                "assignment_ids": [181],
                "assignment_candidate_ids": [131],
                "chat_group_ids": [191],
                "chat_message_ids": [151],
                "default_group_id": 51,
                "reference_projector_id": 71,
                "motions_default_workflow_id": 211,
                "motions_default_amendment_workflow_id": 211,
                "motions_default_statute_amendment_workflow_id": 211,
                "logo_$_id": [
                    "projector_main",
                    "projector_header",
                    "web_header",
                    "pdf_header_l",
                    "pdf_header_r",
                    "pdf_footer_l",
                    "pdf_footer_r",
                    "pdf_ballot_paper",
                ],
                "logo_$projector_main_id": 31,
                "logo_$projector_header_id": 31,
                "logo_$web_header_id": 31,
                "logo_$pdf_header_l_id": 31,
                "logo_$pdf_header_r_id": 31,
                "logo_$pdf_footer_l_id": 31,
                "logo_$pdf_footer_r_id": 31,
                "logo_$pdf_ballot_paper_id": 32,
                "font_$_id": [
                    "regular",
                    "italic",
                    "bold",
                    "bold_italic",
                    "monospace",
                    "chyron_speaker_name",
                    "projector_h1",
                    "projector_h2",
                ],
                "font_$regular_id": 33,
                "font_$italic_id": 33,
                "font_$bold_id": 33,
                "font_$bold_italic_id": 33,
                "font_$monospace_id": 33,
                "font_$chyron_speaker_name_id": 33,
                "font_$projector_h1_id": 33,
                "font_$projector_h2_id": 33,
                "default_projector_$_ids": [
                    "agenda_all_items",
                    "topics",
                    "list_of_speakers",
                    "current_list_of_speakers",
                    "motion",
                    "amendment",
                    "motion_block",
                    "assignment",
                    "mediafile",
                    "projector_message",
                    "projector_countdowns",
                    "assignment_poll",
                    "motion_poll",
                    "poll",
                ],
                "default_projector_$agenda_all_items_ids": [71, 72],
                "default_projector_$topics_ids": [71],
                "default_projector_$list_of_speakers_ids": [71],
                "default_projector_$current_list_of_speakers_ids": [71],
                "default_projector_$motion_ids": [71],
                "default_projector_$amendment_ids": [71],
                "default_projector_$motion_block_ids": [71],
                "default_projector_$assignment_ids": [71],
                "default_projector_$mediafile_ids": [71],
                "default_projector_$projector_message_ids": [71],
                "default_projector_$projector_countdowns_ids": [71],
                "default_projector_$assignment_poll_ids": [71],
                "default_projector_$motion_poll_ids": [71],
                "default_projector_$poll_ids": [71],
            },
        },
        {
            "type": "create",
            "fqid": "meeting/42",
            "fields": {
                "id": 42,
                "is_active_in_organization_id": 1,
                "committee_id": 12,
                "motion_ids": [62],
                "group_ids": [53],
                "poll_ids": [82],
                "list_of_speakers_ids": [173],
                "mediafile_ids": [33],
                "motion_workflow_ids": [212],
                "motion_state_ids": [162],
                "projector_ids": [73],
                "default_group_id": 53,
                "reference_projector_id": 73,
                "motions_default_workflow_id": 212,
                "motions_default_amendment_workflow_id": 212,
                "motions_default_statute_amendment_workflow_id": 212,
                "default_projector_$_ids": [],
            },
        },
        # will be deleted in next position
        {
            "type": "create",
            "fqid": "meeting/43",
            "fields": {
                "id": 43,
            },
        },
        # motions
        {
            "type": "create",
            "fqid": "motion/61",
            "fields": {
                "id": 61,
                "meeting_id": 41,
                "sequential_number": 1,
                "title": "title",
                "amendment_paragraphs_$": ["0", "1", "2", "42"],
                "amendment_paragraphs_$0": "change",
                "amendment_paragraphs_$1": "change",
                "amendment_paragraphs_$2": "change",
                "amendment_paragraphs_$42": "change",
                "state_id": 161,
                "list_of_speakers_id": 171,
                "supporter_ids": [221],
                "submitter_ids": [141],
            },
        },
        {
            "type": "create",
            "fqid": "motion/62",
            "fields": {
                "id": 62,
                "meeting_id": 42,
                "sequential_number": 1,
                "title": "title",
                "state_id": 162,
                "list_of_speakers_id": 173,
                "poll_ids": [82],
            },
        },
        # mediafiles
        {
            "type": "create",
            "fqid": "mediafile/31",
            "fields": {
                "id": 31,
                "owner_id": "meeting/41",
                "title": "logo1",
                "is_public": True,
                "used_as_logo_$_in_meeting_id": [
                    "projector_main",
                    "projector_header",
                    "web_header",
                    "pdf_header_l",
                    "pdf_header_r",
                    "pdf_footer_l",
                    "pdf_footer_r",
                ],
                "used_as_logo_$projector_main_in_meeting_id": 41,
                "used_as_logo_$projector_header_in_meeting_id": 41,
                "used_as_logo_$web_header_in_meeting_id": 41,
                "used_as_logo_$pdf_header_l_in_meeting_id": 41,
                "used_as_logo_$pdf_header_r_in_meeting_id": 41,
                "used_as_logo_$pdf_footer_l_in_meeting_id": 41,
                "used_as_logo_$pdf_footer_r_in_meeting_id": 41,
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/32",
            "fields": {
                "id": 32,
                "owner_id": "meeting/41",
                "title": "logo2",
                "is_public": True,
                "used_as_logo_$_in_meeting_id": ["pdf_ballot_paper"],
                "used_as_logo_$pdf_ballot_paper_in_meeting_id": 41,
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/33",
            "fields": {
                "id": 33,
                "owner_id": "meeting/42",
                "title": "font",
                "is_public": True,
                "used_as_font_$_in_meeting_id": [
                    "regular",
                    "italic",
                    "bold",
                    "bold_italic",
                    "monospace",
                    "chyron_speaker_name",
                    "projector_h1",
                    "projector_h2",
                ],
                "used_as_font_$regular_in_meeting_id": 41,
                "used_as_font_$italic_in_meeting_id": 41,
                "used_as_font_$bold_in_meeting_id": 41,
                "used_as_font_$bold_italic_in_meeting_id": 41,
                "used_as_font_$monospace_in_meeting_id": 41,
                "used_as_font_$chyron_speaker_name_in_meeting_id": 41,
                "used_as_font_$projector_h1_in_meeting_id": 41,
                "used_as_font_$projector_h2_in_meeting_id": 41,
            },
        },
        # projectors
        {
            "type": "create",
            "fqid": "projector/71",
            "fields": {
                "id": 71,
                "sequential_number": 1,
                "meeting_id": 41,
                "used_as_reference_projector_meeting_id": 41,
                "used_as_default_$_in_meeting_id": [
                    "agenda_all_items",
                    "topics",
                    "list_of_speakers",
                    "current_list_of_speakers",
                    "motion",
                    "amendment",
                    "motion_block",
                    "assignment",
                    "mediafile",
                    "projector_message",
                    "projector_countdowns",
                    "assignment_poll",
                    "motion_poll",
                    "poll",
                ],
                "used_as_default_$agenda_all_items_in_meeting_id": 41,
                "used_as_default_$topics_in_meeting_id": 41,
                "used_as_default_$list_of_speakers_in_meeting_id": 41,
                "used_as_default_$current_list_of_speakers_in_meeting_id": 41,
                "used_as_default_$motion_in_meeting_id": 41,
                "used_as_default_$amendment_in_meeting_id": 41,
                "used_as_default_$motion_block_in_meeting_id": 41,
                "used_as_default_$assignment_in_meeting_id": 41,
                "used_as_default_$mediafile_in_meeting_id": 41,
                "used_as_default_$projector_message_in_meeting_id": 41,
                "used_as_default_$projector_countdowns_in_meeting_id": 41,
                "used_as_default_$assignment_poll_in_meeting_id": 41,
                "used_as_default_$motion_poll_in_meeting_id": 41,
                "used_as_default_$poll_in_meeting_id": 41,
            },
        },
        {
            "type": "create",
            "fqid": "projector/72",
            "fields": {
                "id": 72,
                "sequential_number": 2,
                "meeting_id": 41,
                "used_as_default_$_in_meeting_id": ["agenda_all_items"],
                "used_as_default_$agenda_all_items_in_meeting_id": 41,
            },
        },
        {
            "type": "create",
            "fqid": "projector/73",
            "fields": {
                "id": 73,
                "sequential_number": 1,
                "meeting_id": 42,
                "used_as_reference_projector_meeting_id": 42,
            },
        },
        # polls
        {
            "type": "create",
            "fqid": "poll/81",
            "fields": {
                "id": 81,
                "sequential_number": 1,
                "meeting_id": 41,
                "content_object_id": "assignment/181",
                "title": "title",
                "type": "analog",
                "backend": "fast",
                "pollmethod": "YN",
                "state": "finished",
                "onehundred_percent_base": "disabled",
                "option_ids": [91, 92],
                "voted_ids": [221],
            },
        },
        {
            "type": "create",
            "fqid": "poll/82",
            "fields": {
                "id": 82,
                "sequential_number": 1,
                "meeting_id": 42,
                "content_object_id": "motion/62",
                "title": "title",
                "type": "analog",
                "backend": "fast",
                "pollmethod": "YN",
                "state": "finished",
                "onehundred_percent_base": "disabled",
                "voted_ids": [221],
            },
        },
        # options
        {
            "type": "create",
            "fqid": "option/91",
            "fields": {
                "id": 91,
                "poll_id": 81,
                "meeting_id": 41,
                "content_object_id": "user/221",
                "vote_ids": [101],
            },
        },
        {
            "type": "create",
            "fqid": "option/92",
            "fields": {
                "id": 92,
                "poll_id": 81,
                "meeting_id": 41,
                "content_object_id": "user/221",
            },
        },
        # votes
        {
            "type": "create",
            "fqid": "vote/101",
            "fields": {
                "id": 101,
                "option_id": 91,
                "meeting_id": 41,
                "user_token": "token",
                "value": "Y",
                "user_id": 221,
                "delegated_user_id": 221,
            },
        },
        # groups
        {
            "type": "create",
            "fqid": "group/51",
            "fields": {
                "id": 51,
                "meeting_id": 41,
                "name": "group1",
                "user_ids": [221, 222],
                "default_group_for_meeting_id": 41,
            },
        },
        {
            "type": "create",
            "fqid": "group/52",
            "fields": {
                "id": 52,
                "meeting_id": 41,
                "name": "group2",
                "user_ids": [221],
            },
        },
        {
            "type": "create",
            "fqid": "group/53",
            "fields": {
                "id": 53,
                "meeting_id": 42,
                "name": "group3",
                "user_ids": [221],
                "default_group_for_meeting_id": 42,
            },
        },
        # speakers
        {
            "type": "create",
            "fqid": "speaker/121",
            "fields": {
                "id": 121,
                "meeting_id": 41,
                "list_of_speakers_id": 171,
                "user_id": 221,
            },
        },
        # lists of speakers
        {
            "type": "create",
            "fqid": "list_of_speakers/171",
            "fields": {
                "id": 171,
                "sequential_number": 1,
                "meeting_id": 41,
                "content_object_id": "motion/61",
                "speaker_ids": [121],
            },
        },
        {
            "type": "create",
            "fqid": "list_of_speakers/172",
            "fields": {
                "id": 172,
                "sequential_number": 2,
                "meeting_id": 41,
                "content_object_id": "assignment/181",
            },
        },
        {
            "type": "create",
            "fqid": "list_of_speakers/173",
            "fields": {
                "id": 173,
                "sequential_number": 1,
                "meeting_id": 42,
                "content_object_id": "motion/62",
            },
        },
        # personal notes
        {
            "type": "create",
            "fqid": "personal_note/111",
            "fields": {
                "id": 111,
                "meeting_id": 41,
                "user_id": 221,
            },
        },
        # motion submitters
        {
            "type": "create",
            "fqid": "motion_submitter/141",
            "fields": {
                "id": 141,
                "meeting_id": 41,
                "motion_id": 61,
                "user_id": 221,
            },
        },
        # assignment candidates
        {
            "type": "create",
            "fqid": "assignment_candidate/131",
            "fields": {
                "id": 131,
                "meeting_id": 41,
                "assignment_id": 181,
                "user_id": 221,
            },
        },
        # assignments
        {
            "type": "create",
            "fqid": "assignment/181",
            "fields": {
                "id": 181,
                "sequential_number": 1,
                "meeting_id": 41,
                "title": "assignment",
                "candidate_ids": [131],
                "list_of_speakers_id": 172,
                "poll_ids": [81],
            },
        },
        # chat messages
        {
            "type": "create",
            "fqid": "chat_message/151",
            "fields": {
                "id": 151,
                "meeting_id": 41,
                "user_id": 221,
                "chat_group_id": 191,
                "content": "message",
                "created": 1684938947,
            },
        },
        # chat groups
        {
            "type": "create",
            "fqid": "chat_group/191",
            "fields": {
                "id": 191,
                "meeting_id": 41,
                "chat_message_ids": [151],
                "name": "chat group",
            },
        },
        # motion workflows
        {
            "type": "create",
            "fqid": "motion_workflow/211",
            "fields": {
                "id": 211,
                "meeting_id": 41,
                "default_workflow_meeting_id": 41,
                "default_amendment_workflow_meeting_id": 41,
                "default_statute_amendment_workflow_meeting_id": 41,
                "name": "workflow",
                "sequential_number": 1,
                "first_state_id": 161,
                "state_ids": [161],
            },
        },
        {
            "type": "create",
            "fqid": "motion_workflow/212",
            "fields": {
                "id": 212,
                "meeting_id": 42,
                "default_workflow_meeting_id": 42,
                "default_amendment_workflow_meeting_id": 42,
                "default_statute_amendment_workflow_meeting_id": 42,
                "name": "workflow",
                "sequential_number": 1,
                "first_state_id": 162,
                "state_ids": [162],
            },
        },
        # motion states
        {
            "type": "create",
            "fqid": "motion_state/161",
            "fields": {
                "id": 161,
                "meeting_id": 41,
                "name": "state",
                "weight": 1,
                "css_class": "lightblue",
                "workflow_id": 211,
                "first_state_of_workflow_id": 211,
                "motion_ids": [61],
            },
        },
        {
            "type": "create",
            "fqid": "motion_state/162",
            "fields": {
                "id": 162,
                "meeting_id": 42,
                "name": "state",
                "weight": 1,
                "css_class": "lightblue",
                "workflow_id": 212,
                "first_state_of_workflow_id": 212,
                "motion_ids": [62],
            },
        },
    )
    write(
        {
            "type": "delete",
            "fqid": "meeting/43",
        }
    )
    finalize("0044_remove_template_fields")

    assert_model(
        "organization/1",
        {
            "id": 1,
            "default_language": "en",
            "theme_id": 201,
            "theme_ids": [201],
            "user_ids": [221, 222, 223, 224],
            "committee_ids": [11, 12],
            "active_meeting_ids": [41, 42],
        },
    )
    assert_model(
        "theme/201",
        {
            "id": 201,
            "name": "theme",
            "accent_500": "#000000",
            "primary_500": "#000000",
            "warn_500": "#000000",
            "theme_for_organization_id": 1,
            "organization_id": 1,
        },
    )
    assert_model(
        "user/221",
        {
            "id": 221,
            "organization_id": 1,
            "username": "user1",
            "committee_management_ids": [11],
            "poll_voted_ids": [81, 82],
            "option_ids": [91, 92],
            "vote_ids": [101],
            "delegated_vote_ids": [101],
            "meeting_user_ids": [1, 2],
        },
    )
    assert_model(
        "meeting_user/1",
        {
            "id": 1,
            "meeting_id": 41,
            "user_id": 221,
            "comment": "comment",
            "number": "number",
            "structure_level": "structure level",
            "about_me": "about me",
            "vote_weight": "1.234567",
            "group_ids": [51, 52],
            "speaker_ids": [121],
            "personal_note_ids": [111],
            "supported_motion_ids": [61],
            "motion_submitter_ids": [141],
            "assignment_candidate_ids": [131],
            "vote_delegated_to_id": 3,
            "chat_message_ids": [151],
        },
    )
    assert_model(
        "meeting_user/2",
        {
            "id": 2,
            "meeting_id": 42,
            "user_id": 221,
            "group_ids": [53],
        },
    )
    assert_model(
        "user/222",
        {
            "id": 222,
            "organization_id": 1,
            "username": "user2",
            "meeting_user_ids": [3],
        },
    )
    assert_model(
        "meeting_user/3",
        {
            "id": 3,
            "meeting_id": 41,
            "user_id": 222,
            "group_ids": [51],
            "vote_delegations_from_ids": [1],
        },
    )
    assert_model(
        "user/223",
        {
            "id": 223,
            "organization_id": 1,
            "username": "user3",
        },
    )
    assert_model("meeting_user/4", DoesNotExist())
    assert_model(
        "user/224",
        {
            "id": 224,
            "organization_id": 1,
            "username": "user4",
        },
    )
    assert_model(
        "committee/11",
        {
            "id": 11,
            "organization_id": 1,
            "name": "committee1",
            "manager_ids": [221],
            "meeting_ids": [41],
        },
    )
    assert_model(
        "committee/12",
        {
            "id": 12,
            "organization_id": 1,
            "name": "committee2",
            # orphan structured field - will be kept
            "user_$can_manage_management_level": [221],
            "meeting_ids": [42],
        },
    )
    assert_model(
        "meeting/41",
        {
            "id": 41,
            "is_active_in_organization_id": 1,
            "committee_id": 11,
            "meeting_user_ids": [1, 3],
            "motion_ids": [61],
            "mediafile_ids": [31, 32],
            "projector_ids": [71, 72],
            "group_ids": [51, 52],
            "poll_ids": [81],
            "option_ids": [91, 92],
            "vote_ids": [101],
            "speaker_ids": [121],
            "list_of_speakers_ids": [171, 172],
            "personal_note_ids": [111],
            "motion_submitter_ids": [141],
            "motion_workflow_ids": [211],
            "motion_state_ids": [161],
            "assignment_ids": [181],
            "assignment_candidate_ids": [131],
            "chat_group_ids": [191],
            "chat_message_ids": [151],
            "default_group_id": 51,
            "reference_projector_id": 71,
            "motions_default_workflow_id": 211,
            "motions_default_amendment_workflow_id": 211,
            "motions_default_statute_amendment_workflow_id": 211,
            "logo_projector_main_id": 31,
            "logo_projector_header_id": 31,
            "logo_web_header_id": 31,
            "logo_pdf_header_l_id": 31,
            "logo_pdf_header_r_id": 31,
            "logo_pdf_footer_l_id": 31,
            "logo_pdf_footer_r_id": 31,
            "logo_pdf_ballot_paper_id": 32,
            "font_regular_id": 33,
            "font_italic_id": 33,
            "font_bold_id": 33,
            "font_bold_italic_id": 33,
            "font_monospace_id": 33,
            "font_chyron_speaker_name_id": 33,
            "font_projector_h1_id": 33,
            "font_projector_h2_id": 33,
            "default_projector_agenda_item_list_ids": [71, 72],
            "default_projector_topic_ids": [71],
            "default_projector_list_of_speakers_ids": [71],
            "default_projector_current_list_of_speakers_ids": [71],
            "default_projector_motion_ids": [71],
            "default_projector_amendment_ids": [71],
            "default_projector_motion_block_ids": [71],
            "default_projector_assignment_ids": [71],
            "default_projector_mediafile_ids": [71],
            "default_projector_message_ids": [71],
            "default_projector_countdown_ids": [71],
            "default_projector_assignment_poll_ids": [71],
            "default_projector_motion_poll_ids": [71],
            "default_projector_poll_ids": [71],
        },
    )
    assert_model(
        "meeting/42",
        {
            "id": 42,
            "is_active_in_organization_id": 1,
            "committee_id": 12,
            "meeting_user_ids": [2],
            "motion_ids": [62],
            "group_ids": [53],
            "poll_ids": [82],
            "list_of_speakers_ids": [173],
            "mediafile_ids": [33],
            "motion_workflow_ids": [212],
            "motion_state_ids": [162],
            "projector_ids": [73],
            "default_group_id": 53,
            "reference_projector_id": 73,
            "motions_default_workflow_id": 212,
            "motions_default_amendment_workflow_id": 212,
            "motions_default_statute_amendment_workflow_id": 212,
        },
    )
    meeting = read_model("meeting/43")
    assert meeting["meta_deleted"] is True
    assert_model(
        "motion/61",
        {
            "id": 61,
            "meeting_id": 41,
            "sequential_number": 1,
            "title": "title",
            "amendment_paragraphs": {
                "0": "change",
                "1": "change",
                "2": "change",
                "42": "change",
            },
            "state_id": 161,
            "list_of_speakers_id": 171,
            "supporter_meeting_user_ids": [1],
            "submitter_ids": [141],
        },
    )
    assert_model(
        "motion/62",
        {
            "id": 62,
            "meeting_id": 42,
            "sequential_number": 1,
            "title": "title",
            "state_id": 162,
            "list_of_speakers_id": 173,
            "poll_ids": [82],
        },
    )
    assert_model(
        "mediafile/31",
        {
            "id": 31,
            "owner_id": "meeting/41",
            "title": "logo1",
            "is_public": True,
            "used_as_logo_projector_main_in_meeting_id": 41,
            "used_as_logo_projector_header_in_meeting_id": 41,
            "used_as_logo_web_header_in_meeting_id": 41,
            "used_as_logo_pdf_header_l_in_meeting_id": 41,
            "used_as_logo_pdf_header_r_in_meeting_id": 41,
            "used_as_logo_pdf_footer_l_in_meeting_id": 41,
            "used_as_logo_pdf_footer_r_in_meeting_id": 41,
        },
    )
    assert_model(
        "mediafile/32",
        {
            "id": 32,
            "owner_id": "meeting/41",
            "title": "logo2",
            "is_public": True,
            "used_as_logo_pdf_ballot_paper_in_meeting_id": 41,
        },
    )
    assert_model(
        "mediafile/33",
        {
            "id": 33,
            "owner_id": "meeting/42",
            "title": "font",
            "is_public": True,
            "used_as_font_regular_in_meeting_id": 41,
            "used_as_font_italic_in_meeting_id": 41,
            "used_as_font_bold_in_meeting_id": 41,
            "used_as_font_bold_italic_in_meeting_id": 41,
            "used_as_font_monospace_in_meeting_id": 41,
            "used_as_font_chyron_speaker_name_in_meeting_id": 41,
            "used_as_font_projector_h1_in_meeting_id": 41,
            "used_as_font_projector_h2_in_meeting_id": 41,
        },
    )
    assert_model(
        "projector/71",
        {
            "id": 71,
            "sequential_number": 1,
            "meeting_id": 41,
            "used_as_reference_projector_meeting_id": 41,
            "used_as_default_projector_for_agenda_item_list_in_meeting_id": 41,
            "used_as_default_projector_for_topic_in_meeting_id": 41,
            "used_as_default_projector_for_list_of_speakers_in_meeting_id": 41,
            "used_as_default_projector_for_current_list_of_speakers_in_meeting_id": 41,
            "used_as_default_projector_for_motion_in_meeting_id": 41,
            "used_as_default_projector_for_amendment_in_meeting_id": 41,
            "used_as_default_projector_for_motion_block_in_meeting_id": 41,
            "used_as_default_projector_for_assignment_in_meeting_id": 41,
            "used_as_default_projector_for_mediafile_in_meeting_id": 41,
            "used_as_default_projector_for_message_in_meeting_id": 41,
            "used_as_default_projector_for_countdown_in_meeting_id": 41,
            "used_as_default_projector_for_assignment_poll_in_meeting_id": 41,
            "used_as_default_projector_for_motion_poll_in_meeting_id": 41,
            "used_as_default_projector_for_poll_in_meeting_id": 41,
        },
    )
    assert_model(
        "projector/72",
        {
            "id": 72,
            "sequential_number": 2,
            "meeting_id": 41,
            "used_as_default_projector_for_agenda_item_list_in_meeting_id": 41,
        },
    )
    assert_model(
        "projector/73",
        {
            "id": 73,
            "sequential_number": 1,
            "meeting_id": 42,
            "used_as_reference_projector_meeting_id": 42,
        },
    )
    assert_model(
        "poll/81",
        {
            "id": 81,
            "sequential_number": 1,
            "meeting_id": 41,
            "content_object_id": "assignment/181",
            "title": "title",
            "type": "analog",
            "backend": "fast",
            "pollmethod": "YN",
            "state": "finished",
            "onehundred_percent_base": "disabled",
            "option_ids": [91, 92],
            "voted_ids": [221],
        },
    )
    assert_model(
        "poll/82",
        {
            "id": 82,
            "sequential_number": 1,
            "meeting_id": 42,
            "content_object_id": "motion/62",
            "title": "title",
            "type": "analog",
            "backend": "fast",
            "pollmethod": "YN",
            "state": "finished",
            "onehundred_percent_base": "disabled",
            "voted_ids": [221],
        },
    )
    assert_model(
        "option/91",
        {
            "id": 91,
            "poll_id": 81,
            "meeting_id": 41,
            "content_object_id": "user/221",
            "vote_ids": [101],
        },
    )
    assert_model(
        "option/92",
        {
            "id": 92,
            "poll_id": 81,
            "meeting_id": 41,
            "content_object_id": "user/221",
        },
    )
    assert_model(
        "vote/101",
        {
            "id": 101,
            "option_id": 91,
            "meeting_id": 41,
            "user_token": "token",
            "value": "Y",
            "user_id": 221,
            "delegated_user_id": 221,
        },
    )
    assert_model(
        "group/51",
        {
            "id": 51,
            "meeting_id": 41,
            "name": "group1",
            "meeting_user_ids": [1, 3],
            "default_group_for_meeting_id": 41,
        },
    )
    assert_model(
        "group/52",
        {
            "id": 52,
            "meeting_id": 41,
            "name": "group2",
            "meeting_user_ids": [1],
        },
    )
    assert_model(
        "group/53",
        {
            "id": 53,
            "meeting_id": 42,
            "name": "group3",
            "meeting_user_ids": [2],
            "default_group_for_meeting_id": 42,
        },
    )
    assert_model(
        "speaker/121",
        {
            "id": 121,
            "meeting_id": 41,
            "list_of_speakers_id": 171,
            "meeting_user_id": 1,
        },
    )
    assert_model(
        "list_of_speakers/171",
        {
            "id": 171,
            "sequential_number": 1,
            "meeting_id": 41,
            "content_object_id": "motion/61",
            "speaker_ids": [121],
        },
    )
    assert_model(
        "list_of_speakers/172",
        {
            "id": 172,
            "sequential_number": 2,
            "meeting_id": 41,
            "content_object_id": "assignment/181",
        },
    )
    assert_model(
        "list_of_speakers/173",
        {
            "id": 173,
            "sequential_number": 1,
            "meeting_id": 42,
            "content_object_id": "motion/62",
        },
    )
    assert_model(
        "personal_note/111",
        {
            "id": 111,
            "meeting_id": 41,
            "meeting_user_id": 1,
        },
    )
    assert_model(
        "motion_submitter/141",
        {
            "id": 141,
            "meeting_id": 41,
            "motion_id": 61,
            "meeting_user_id": 1,
        },
    )
    assert_model(
        "assignment_candidate/131",
        {
            "id": 131,
            "meeting_id": 41,
            "assignment_id": 181,
            "meeting_user_id": 1,
        },
    )
    assert_model(
        "assignment/181",
        {
            "id": 181,
            "sequential_number": 1,
            "meeting_id": 41,
            "title": "assignment",
            "candidate_ids": [131],
            "list_of_speakers_id": 172,
            "poll_ids": [81],
        },
    )
    assert_model(
        "chat_message/151",
        {
            "id": 151,
            "meeting_id": 41,
            "meeting_user_id": 1,
            "chat_group_id": 191,
            "content": "message",
            "created": 1684938947,
        },
    )
    assert_model(
        "chat_group/191",
        {
            "id": 191,
            "meeting_id": 41,
            "chat_message_ids": [151],
            "name": "chat group",
        },
    )
    assert_model(
        "motion_workflow/211",
        {
            "id": 211,
            "meeting_id": 41,
            "default_workflow_meeting_id": 41,
            "default_amendment_workflow_meeting_id": 41,
            "default_statute_amendment_workflow_meeting_id": 41,
            "name": "workflow",
            "sequential_number": 1,
            "first_state_id": 161,
            "state_ids": [161],
        },
    )
    assert_model(
        "motion_workflow/212",
        {
            "id": 212,
            "meeting_id": 42,
            "default_workflow_meeting_id": 42,
            "default_amendment_workflow_meeting_id": 42,
            "default_statute_amendment_workflow_meeting_id": 42,
            "name": "workflow",
            "sequential_number": 1,
            "first_state_id": 162,
            "state_ids": [162],
        },
    )
    assert_model(
        "motion_state/161",
        {
            "id": 161,
            "meeting_id": 41,
            "name": "state",
            "weight": 1,
            "css_class": "lightblue",
            "workflow_id": 211,
            "first_state_of_workflow_id": 211,
            "motion_ids": [61],
        },
    )
    assert_model(
        "motion_state/162",
        {
            "id": 162,
            "meeting_id": 42,
            "name": "state",
            "weight": 1,
            "css_class": "lightblue",
            "workflow_id": 212,
            "first_state_of_workflow_id": 212,
            "motion_ids": [62],
        },
    )
