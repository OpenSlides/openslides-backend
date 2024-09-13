def create_comprehensive_data(write) -> None:
    write(
        {
            "type": "create",
            "fqid": "meeting/11",
            "fields": {
                "id": 11,
                "name": "string",
                "language": "string",
                "motions_statutes_enabled": True,
                "motions_statute_recommendations_by": 12,
                "motion_statute_paragraph_ids": [1, 2],
                "motion_ids": [1, 2],
                "motion_workflow_ids": [1],
                "motion_state_ids": [1],
                "motion_category_ids": [1],
                "motion_block_ids": [1],
                "meeting_user_ids": [1, 2],
                "tag_ids": [1, 2],
                "mediafile_ids": [1],
                "motion_working_group_speaker_ids": [1],
                "motion_change_recommendation_ids": [1],
                "motion_submitter_ids": [1],
                "motion_editor_ids": [1],
                "motion_comment_ids": [1],
                "motion_comment_section_ids": [1],
                "all_projection_ids": [1, 2, 3, 4, 5, 6, 7],
                "projector_ids": [1, 2],
                "personal_note_ids": [1],
                "group_ids": [1],
                "poll_candidate_list_ids": [1],
                "vote_ids": [1],
                "option_ids": [1],
                "poll_ids": [1],
                "agenda_item_ids": [1, 2, 3],
                "topic_ids": [1],
                "list_of_speakers_ids": [1],
                "structure_level_ids": [1],
                "speaker_ids": [1],
                "point_of_order_category_ids": [1],
            },
        },
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {
                "id": 1,
                "statute_paragraph_id": 1,
                "title": "text",
                "recommendation_id": 1,
                "state_extension_reference_ids": ["motion/2"],
                "referenced_in_motion_state_extension_ids": [2],
                "recommendation_extension_reference_ids": ["motion/2"],
                "referenced_in_motion_recommendation_extension_ids": [2],
                "category_id": 1,
                "block_id": 1,
                "supporter_meeting_user_ids": [1],
                "tag_ids": [1],
                "attachment_ids": [1],
                "submitter_ids": [1],
                "editor_ids": [1],
                "comment_ids": [1],
                "projection_ids": [1],
                "personal_note_ids": [1],
                "option_ids": [1, 2, 3],
                "poll_ids": [1],
                "agenda_item_id": 2,
                "list_of_speakers_id": 1,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "motion/2",
            "fields": {
                "id": 2,
                "statute_paragraph_id": 2,
                "title": "text",
                "meeting_id": 11,
                "recommendation_id": 1,
                "state_extension_reference_ids": ["motion/1"],
                "referenced_in_motion_state_extension_ids": [1],
                "recommendation_extension_reference_ids": ["motion/1"],
                "referenced_in_motion_recommendation_extension_ids": [1],
                "working_group_speaker_ids": [1],
                "change_recommendation_ids": [1],
                "agenda_item_id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "motion_category/1",
            "fields": {"id": 1, "name": "AA", "meeting_id": 11, "motion_ids": [1]},
        },
        {
            "type": "create",
            "fqid": "motion_block/1",
            "fields": {"id": 1, "name": "AA", "meeting_id": 11, "motion_ids": [1]},
        },
        {
            "type": "create",
            "fqid": "meeting_user/1",
            "fields": {
                "id": 1,
                "user_id": 1,
                "motion_editor_ids": [1],
                "motion_submitter_ids": [1],
                "motion_working_group_speaker_ids": [1],
                "supported_motion_ids": [1],
                "speaker_ids": [1],
                "personal_note_ids": [1],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "meeting_user/2",
            "fields": {
                "id": 2,
                "user_id": 2,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "user/1",
            "fields": {
                "id": 1,
                "meeting_ids": [11],
                "meeting_user_ids": [1],
                "poll_voted_ids": [1],
                "vote_ids": [1],
                "option_ids": [2],
            },
        },
        {
            "type": "create",
            "fqid": "user/2",
            "fields": {
                "id": 2,
                "meeting_ids": [11],
                "meeting_user_ids": [2],
                "delegated_vote_ids": [1],
            },
        },
        {
            "type": "create",
            "fqid": "tag/1",
            "fields": {
                "id": 1,
                "name": "A Tag",
                "meeting_id": 11,
                "tagged_ids": ["motion/1", "agenda_item/3"],
            },
        },
        {
            "type": "create",
            "fqid": "tag/2",
            "fields": {
                "id": 2,
                "name": "A 2nd Tag",
                "meeting_id": 11,
                "tagged_ids": ["agenda_item/1", "agenda_item/2"],
            },
        },
        {
            "type": "create",
            "fqid": "mediafile/1",
            "fields": {
                "id": 1,
                "title": "A Media Attachment",
                "owner_id": "meeting/11",
                "is_public": True,
                "attachment_ids": ["motion/1"],
            },
        },
        {
            "type": "create",
            "fqid": "motion_submitter/1",
            "fields": {"id": 1, "meeting_user_id": 1, "motion_id": 1, "meeting_id": 11},
        },
        {
            "type": "create",
            "fqid": "motion_editor/1",
            "fields": {"id": 1, "meeting_user_id": 1, "motion_id": 1, "meeting_id": 11},
        },
        {
            "type": "create",
            "fqid": "motion_working_group_speaker/1",
            "fields": {"id": 1, "meeting_user_id": 1, "motion_id": 1, "meeting_id": 11},
        },
        {
            "type": "create",
            "fqid": "motion_change_recommendation/1",
            "fields": {
                "id": 1,
                "line_from": 1,
                "line_to": 5,
                "text": "HTML",
                "motion_id": 2,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "motion_comment/1",
            "fields": {
                "id": 1,
                "comment": "HTML",
                "motion_id": 1,
                "section_id": 1,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "motion_comment_section/1",
            "fields": {
                "id": 1,
                "name": "A Comment Section",
                "comment_ids": [1],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "projection/1",
            "fields": {
                "id": 1,
                "content_object_id": "motion/1",
                "current_projector_id": 1,
                "preview_projector_id": 1,
                "history_projector_id": 2,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "projection/2",
            "fields": {
                "id": 2,
                "content_object_id": "poll/1",
                "current_projector_id": 1,
                "history_projector_id": 2,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "projection/3",
            "fields": {
                "id": 3,
                "content_object_id": "agenda_item/1",
                "current_projector_id": 1,
                "preview_projector_id": 2,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "projection/4",
            "fields": {
                "id": 4,
                "content_object_id": "agenda_item/2",
                "current_projector_id": 2,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "projection/5",
            "fields": {
                "id": 5,
                "content_object_id": "agenda_item/3",
                "history_projector_id": 1,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "projection/6",
            "fields": {
                "id": 6,
                "content_object_id": "topic/1",
                "history_projector_id": 1,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "projection/7",
            "fields": {
                "id": 7,
                "content_object_id": "list_of_speakers/1",
                "preview_projector_id": 2,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "projector/1",
            "fields": {
                "id": 1,
                "current_projection_ids": [1, 2, 3],
                "preview_projection_ids": [1],
                "history_projection_ids": [5, 6],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "projector/2",
            "fields": {
                "id": 2,
                "current_projection_ids": [4],
                "preview_projection_ids": [3, 7],
                "history_projection_ids": [1, 2],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "personal_note/1",
            "fields": {
                "id": 1,
                "meeting_user_id": 1,
                "content_object_id": "motion/1",
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "poll/1",
            "fields": {
                "id": 1,
                "content_object_id": "motion/1",
                "option_ids": [1, 2, 3],
                "global_option_id": 1,
                "voted_ids": [1],
                "entitled_group_ids": [1],
                "projection_ids": [2],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "option/1",
            "fields": {
                "id": 1,
                "content_object_id": "motion/1",
                "used_as_global_option_in_poll_id": 1,
                "vote_ids": [1],
                "poll_id": 1,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "option/2",
            "fields": {
                "id": 2,
                "content_object_id": "user/1",
                "vote_ids": [],
                "poll_id": 1,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "option/3",
            "fields": {
                "id": 3,
                "content_object_id": "poll_candidate_list/1",
                "vote_ids": [],
                "poll_id": 1,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "vote/1",
            "fields": {
                "id": 1,
                "delegated_user_id": 2,
                "user_id": 1,
                "meeting_id": 11,
                "option_id": 1,
            },
        },
        {
            "type": "create",
            "fqid": "poll_candidate_list/1",
            "fields": {
                "id": 1,
                "option_id": 3,
                "entries": {"user_id": 1, "weight": 20},
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "group/1",
            "fields": {
                "id": 1,
                "poll_ids": [1],
                "name": "A Group",
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "agenda_item/1",
            "fields": {
                "id": 1,
                "content_object_id": "motion/2",
                "parent_id": None,
                "child_ids": [2],
                "tag_ids": [2],
                "projection_ids": [3],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "agenda_item/2",
            "fields": {
                "id": 2,
                "content_object_id": "motion/1",
                "parent_id": 1,
                "child_ids": [3],
                "tag_ids": [2],
                "projection_ids": [4],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "agenda_item/3",
            "fields": {
                "id": 3,
                "content_object_id": "topic/1",
                "parent_id": 2,
                "child_ids": [],
                "tag_ids": [1],
                "projection_ids": [5],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "topic/1",
            "fields": {
                "id": 1,
                "title": "A tropical topic",
                "agenda_item_id": 3,
                "projection_ids": [6],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "list_of_speakers/1",
            "fields": {
                "id": 1,
                "content_object_id": "motion/1",
                "speaker_ids": [1],
                "structure_level_list_of_speakers_ids": [1],
                "projection_ids": [7],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "structure_level_list_of_speakers/1",
            "fields": {
                "id": 1,
                "structure_level_id": 1,
                "list_of_speakers_id": 1,
                "initial_time": 30,
                "speaker_ids": [1],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "structure_level/1",
            "fields": {
                "id": 1,
                "name": "ErstePartei",
                "color": "#FF0000",
                "default_time": 30,
                "structure_level_list_of_speakers_ids": [1],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "speaker/1",
            "fields": {
                "id": 1,
                "meeting_user_id": 1,
                "point_of_order_category_id": 1,
                "list_of_speakers_id": 1,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "point_of_order_category/1",
            "fields": {
                "id": 1,
                "text": "A point of order category",
                "speaker_ids": [1],
                "rank": 1,
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "motion_workflow/1",
            "fields": {
                "id": 1,
                "default_statute_amendment_workflow_meeting_id": 11,
                "state_ids": [1],
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "motion_statute_paragraph/1",
            "fields": {
                "id": 1,
                "title": "string",
                "text": "HTML",
                "meeting_id": 11,
                "motion_ids": [1],
            },
        },
        {
            "type": "create",
            "fqid": "motion_statute_paragraph/2",
            "fields": {
                "id": 2,
                "title": "string",
                "text": "HTML",
                "meeting_id": 11,
                "motion_ids": [2],
            },
        },
        {
            "type": "create",
            "fqid": "motion_state/1",
            "fields": {
                "id": 1,
                "name": "string",
                "workflow_id": 1,
                "motion_recommendation_ids": [1, 2],
                "meeting_id": 11,
            },
        },
    )


def test_no_delete_without_statute(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/11",
            "fields": {
                "id": 11,
                "name": "string",
                "language": "string",
                "motion_ids": [1, 2],
            },
        },
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {
                "id": 1,
                "title": "text",
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "motion/2",
            "fields": {
                "id": 2,
                "title": "text",
                "meeting_id": 11,
            },
        },
    )
    finalize("0054_remove_statutes")
    assert_model(
        "motion/2",
        {
            "id": 2,
            "title": "text",
            "meeting_id": 11,
        },
    )
    assert_model(
        "motion/1",
        {
            "id": 1,
            "title": "text",
            "meeting_id": 11,
        },
    )


def test_delete_motion_without_sideffects(write, finalize, assert_model):
    write(
        {
            "type": "create",
            "fqid": "meeting/11",
            "fields": {
                "id": 11,
                "name": "string",
                "language": "string",
                "motions_statutes_enabled": True,
                "motions_statute_recommendations_by": 12,
                "motion_statute_paragraph_ids": [1],
                "motion_ids": [1, 2],
            },
        },
        {
            "type": "create",
            "fqid": "motion/1",
            "fields": {
                "id": 1,
                "statute_paragraph_id": 1,
                "title": "text",
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "motion/2",
            "fields": {
                "id": 2,
                "title": "text",
                "meeting_id": 11,
            },
        },
        {
            "type": "create",
            "fqid": "motion_statute_paragraph/1",
            "fields": {
                "id": 1,
                "title": "string",
                "text": "HTML",
                "meeting_id": 11,
                "motion_ids": [1],
            },
        },
    )
    finalize("0054_remove_statutes")
    assert_model(
        "motion/2",
        {
            "id": 2,
            "title": "text",
            "meeting_id": 11,
        },
    )
    assert_model(
        "motion/1",
        {
            "id": 1,
            "statute_paragraph_id": 1,
            "title": "text",
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )


def test_delete_motion_without_sideffects_to_submodels(write, finalize, assert_model):
    create_comprehensive_data(write)
    data = {
        "motion/3": {
            "id": 3,
            "title": "text",
            "recommendation_id": 2,
            "state_extension_reference_ids": ["motion/4"],
            "referenced_in_motion_state_extension_ids": [4],
            "recommendation_extension_reference_ids": ["motion/4"],
            "referenced_in_motion_recommendation_extension_ids": [4],
            "category_id": 1,
            "block_id": 2,
            "supporter_meeting_user_ids": [1],
            "tag_ids": [1],
            "attachment_ids": [2],
            "working_group_speaker_ids": [2],
            "submitter_ids": [2],
            "editor_ids": [2],
            "comment_ids": [2],
            "projection_ids": [11],
            "personal_note_ids": [2],
            "option_ids": [11],
            "poll_ids": [2],
            "agenda_item_id": 12,
            "list_of_speakers_id": 2,
            "meeting_id": 11,
        },
        "motion/4": {
            "id": 4,
            "title": "text",
            "recommendation_id": 2,
            "state_extension_reference_ids": ["motion/3"],
            "referenced_in_motion_state_extension_ids": [3],
            "recommendation_extension_reference_ids": ["motion/3"],
            "referenced_in_motion_recommendation_extension_ids": [3],
            "change_recommendation_ids": [2],
            "agenda_item_id": 11,
            "meeting_id": 11,
        },
        "motion_block/2": {"id": 2, "name": "AA", "meeting_id": 11, "motion_ids": [3]},
        "mediafile/2": {
            "id": 2,
            "title": "A Media Attachment",
            "owner_id": "meeting/11",
            "is_public": True,
            "attachment_ids": ["motion/3"],
        },
        "motion_submitter/2": {
            "id": 2,
            "meeting_user_id": 1,
            "motion_id": 3,
            "meeting_id": 11,
        },
        "motion_editor/2": {
            "id": 2,
            "meeting_user_id": 1,
            "motion_id": 3,
            "meeting_id": 11,
        },
        "motion_working_group_speaker/2": {
            "id": 2,
            "meeting_user_id": 1,
            "motion_id": 3,
            "meeting_id": 11,
        },
        "motion_change_recommendation/2": {
            "id": 2,
            "line_from": 1,
            "line_to": 5,
            "text": "HTML",
            "motion_id": 4,
            "meeting_id": 11,
        },
        "motion_comment/2": {
            "id": 2,
            "comment": "HTML",
            "motion_id": 3,
            "section_id": 2,
            "meeting_id": 11,
        },
        "motion_comment_section/2": {
            "id": 2,
            "name": "A Comment Section",
            "comment_ids": [2],
            "meeting_id": 11,
        },
        "projection/11": {
            "id": 11,
            "content_object_id": "motion/3",
            "current_projector_id": 3,
            "preview_projector_id": 3,
            "history_projector_id": 4,
            "meeting_id": 11,
        },
        "projection/12": {
            "id": 12,
            "content_object_id": "poll/2",
            "current_projector_id": 3,
            "history_projector_id": 4,
            "meeting_id": 11,
        },
        "projection/13": {
            "id": 13,
            "content_object_id": "agenda_item/11",
            "current_projector_id": 3,
            "preview_projector_id": 4,
            "meeting_id": 11,
        },
        "projection/14": {
            "id": 14,
            "content_object_id": "agenda_item/12",
            "current_projector_id": 4,
            "meeting_id": 11,
        },
        "projection/15": {
            "id": 15,
            "content_object_id": "agenda_item/13",
            "history_projector_id": 3,
            "meeting_id": 11,
        },
        "projection/16": {
            "id": 16,
            "content_object_id": "topic/2",
            "history_projector_id": 3,
            "meeting_id": 11,
        },
        "projection/17": {
            "id": 17,
            "content_object_id": "list_of_speakers/2",
            "preview_projector_id": 4,
            "meeting_id": 11,
        },
        "projector/3": {
            "id": 3,
            "current_projection_ids": [11, 12, 13],
            "preview_projection_ids": [11],
            "history_projection_ids": [15, 16],
            "meeting_id": 11,
        },
        "projector/4": {
            "id": 4,
            "current_projection_ids": [14],
            "preview_projection_ids": [13, 17],
            "history_projection_ids": [11, 12],
            "meeting_id": 11,
        },
        "personal_note/2": {
            "id": 2,
            "meeting_user_id": 1,
            "content_object_id": "motion/3",
            "meeting_id": 11,
        },
        "poll/2": {
            "id": 2,
            "content_object_id": "motion/3",
            "option_ids": [11, 12, 13],
            "global_option_id": 11,
            "voted_ids": [1, 2],
            "entitled_group_ids": [1],
            "projection_ids": [12],
            "meeting_id": 11,
        },
        "option/11": {
            "id": 11,
            "content_object_id": "motion/3",
            "used_as_global_option_in_poll_id": 2,
            "vote_ids": [2],
            "poll_id": 2,
            "meeting_id": 11,
        },
        "option/12": {
            "id": 12,
            "content_object_id": "user/1",
            "vote_ids": [],
            "poll_id": 2,
            "meeting_id": 11,
        },
        "option/13": {
            "id": 13,
            "content_object_id": "poll_candidate_list/2",
            "vote_ids": [],
            "poll_id": 2,
            "meeting_id": 11,
        },
        "vote/2": {
            "id": 2,
            "delegated_user_id": 2,
            "user_id": 1,
            "meeting_id": 11,
            "option_id": 11,
        },
        "poll_candidate_list/2": {
            "id": 2,
            "option_id": 13,
            "entries": {"user_id": 1, "weight": 20},
            "meeting_id": 11,
        },
        "agenda_item/11": {
            "id": 11,
            "content_object_id": "motion/4",
            "parent_id": None,
            "child_ids": [12],
            "tag_ids": [2],
            "projection_ids": [13],
            "meeting_id": 11,
        },
        "agenda_item/12": {
            "id": 12,
            "content_object_id": "motion/3",
            "parent_id": 11,
            "child_ids": [13],
            "tag_ids": [2],
            "projection_ids": [14],
            "meeting_id": 11,
        },
        "agenda_item/13": {
            "id": 13,
            "content_object_id": "topic/2",
            "parent_id": 12,
            "child_ids": [],
            "tag_ids": [1],
            "projection_ids": [15],
            "meeting_id": 11,
        },
        "topic/2": {
            "id": 2,
            "title": "A topical tropic",
            "agenda_item_id": 13,
            "projection_ids": [16],
            "meeting_id": 11,
        },
        "list_of_speakers/2": {
            "id": 2,
            "content_object_id": "motion/3",
            "speaker_ids": [2],
            "structure_level_list_of_speakers_ids": [2],
            "projection_ids": [17],
            "meeting_id": 11,
        },
        "structure_level_list_of_speakers/2": {
            "id": 2,
            "structure_level_id": 1,
            "list_of_speakers_id": 2,
            "initial_time": 30,
            "speaker_ids": [2],
            "meeting_id": 11,
        },
        "speaker/2": {
            "id": 2,
            "meeting_user_id": 1,
            "point_of_order_category_id": 2,
            "list_of_speakers_id": 2,
            "structure_level_list_of_speakers_id": 2,
            "meeting_id": 11,
        },
        "point_of_order_category/2": {
            "id": 2,
            "text": "A point of order category",
            "speaker_ids": [2],
            "rank": 1,
            "meeting_id": 11,
        },
        "motion_workflow/2": {
            "id": 2,
            "state_ids": [2],
            "meeting_id": 11,
        },
        "motion_state/2": {
            "id": 2,
            "name": "string",
            "workflow_id": 2,
            "motion_recommendation_ids": [3, 4],
            "meeting_id": 11,
        },
    }
    write(
        {
            "type": "update",
            "fqid": "meeting/11",
            "fields": {
                "motion_ids": [1, 2, 3, 4],
                "motion_workflow_ids": [1, 2],
                "motion_state_ids": [1, 2],
                "motion_block_ids": [1, 2],
                "mediafile_ids": [1, 2],
                "motion_working_group_speaker_ids": [1, 2],
                "motion_change_recommendation_ids": [1, 2],
                "motion_submitter_ids": [1, 2],
                "motion_editor_ids": [1, 2],
                "motion_comment_ids": [1, 2],
                "motion_comment_section_ids": [1, 2],
                "all_projection_ids": [1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 14, 15, 16, 17],
                "projector_ids": [1, 2, 3, 4],
                "personal_note_ids": [1, 2],
                "poll_candidate_list_ids": [1, 2],
                "vote_ids": [1, 2],
                "option_ids": [1, 2, 3, 11, 12, 13],
                "poll_ids": [1, 2],
                "agenda_item_ids": [1, 2, 3, 11, 12, 13],
                "topic_ids": [1, 2],
                "list_of_speakers_ids": [1, 2],
                "structure_level_list_of_speakers_ids": [1, 2],
                "speaker_ids": [1, 2],
                "point_of_order_category_ids": [1, 2],
            },
        },
        {
            "type": "update",
            "fqid": "structure_level/1",
            "fields": {
                "structure_level_list_of_speakers_ids": [1, 2],
            },
        },
        {
            "type": "update",
            "fqid": "motion_category/1",
            "fields": {"motion_ids": [1, 3]},
        },
        {
            "type": "update",
            "fqid": "meeting_user/1",
            "fields": {
                "motion_editor_ids": [1, 2],
                "motion_submitter_ids": [1, 2],
                "motion_working_group_speaker_ids": [1, 2],
                "supported_motion_ids": [1, 3],
                "speaker_ids": [1, 2],
                "personal_note_ids": [1, 2],
                "meeting_id": 11,
            },
        },
        {
            "type": "update",
            "fqid": "user/1",
            "fields": {
                # "motion_ids": [1, 3],
                "poll_voted_ids": [1, 2],
                "vote_ids": [1, 2],
                "option_ids": [2, 12],
            },
        },
        {
            "type": "update",
            "fqid": "user/2",
            "fields": {
                # "motion_ids": [1, 3],
                "delegated_vote_ids": [1, 2],
                "poll_voted_ids": [1, 2],
            },
        },
        {
            "type": "update",
            "fqid": "group/1",
            "fields": {
                "poll_ids": [1, 2],
            },
        },
        {
            "type": "update",
            "fqid": "poll/1",
            "fields": {
                "voted_ids": [1, 2],
            },
        },
        {
            "type": "update",
            "fqid": "tag/1",
            "fields": {
                "tagged_ids": [
                    "motion/1",
                    "agenda_item/3",
                    "motion/3",
                    "agenda_item/13",
                ],
            },
        },
        {
            "type": "update",
            "fqid": "tag/2",
            "fields": {
                "tagged_ids": [
                    "agenda_item/1",
                    "agenda_item/12",
                    "agenda_item/11",
                    "agenda_item/12",
                ],
            },
        },
        *[
            {
                "type": "create",
                "fqid": fqid,
                "fields": fields,
            }
            for fqid, fields in data.items()
        ]
    )
    finalize("0054_remove_statutes")
    assert_model(
        "motion/1",
        {
            "id": 1,
            "statute_paragraph_id": 1,
            "title": "text",
            "agenda_item_id": 2,
            "attachment_ids": [1],
            "block_id": 1,
            "category_id": 1,
            "comment_ids": [1],
            "editor_ids": [1],
            "list_of_speakers_id": 1,
            "option_ids": [1, 2, 3],
            "personal_note_ids": [1],
            "poll_ids": [1],
            "recommendation_extension_reference_ids": ["motion/2"],
            "recommendation_id": 1,
            "referenced_in_motion_recommendation_extension_ids": [2],
            "referenced_in_motion_state_extension_ids": [2],
            "state_extension_reference_ids": ["motion/2"],
            "submitter_ids": [1],
            "supporter_meeting_user_ids": [1],
            "tag_ids": [1],
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion/2",
        {
            "id": 2,
            "title": "text",
            "agenda_item_id": 1,
            "change_recommendation_ids": [1],
            "recommendation_extension_reference_ids": ["motion/1"],
            "recommendation_id": 1,
            "referenced_in_motion_recommendation_extension_ids": [1],
            "referenced_in_motion_state_extension_ids": [1],
            "state_extension_reference_ids": ["motion/1"],
            "statute_paragraph_id": 2,
            "working_group_speaker_ids": [1],
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    for fqid, fields in data.items():
        assert_model(fqid, fields)


def test_two_meetings(write, finalize, assert_model):
    create_comprehensive_data(write)
    write(
        {
            "type": "create",
            "fqid": "meeting/12",
            "fields": {
                "id": 12,
                "name": "string",
                "language": "string",
                "motions_statutes_enabled": True,
                "motions_statute_recommendations_by": 12,
                "motion_statute_paragraph_ids": [3],
                "motion_ids": [3],
                "motion_state_ids": [2],
                "motion_workflow_ids": [2],
            },
        },
        {
            "type": "create",
            "fqid": "motion_statute_paragraph/3",
            "fields": {
                "id": 3,
                "title": "string",
                "text": "HTML",
                "meeting_id": 12,
                "motion_ids": [3],
            },
        },
        {
            "type": "create",
            "fqid": "motion/3",
            "fields": {
                "id": 3,
                "statute_paragraph_id": 3,
                "title": "text",
                "meeting_id": 12,
                "recommendation_id": 2,
            },
        },
        {
            "type": "create",
            "fqid": "motion_workflow/2",
            "fields": {
                "id": 2,
                "default_statute_amendment_workflow_meeting_id": 12,
                "state_ids": [2],
                "meeting_id": 12,
            },
        },
        {
            "type": "create",
            "fqid": "motion_state/2",
            "fields": {
                "id": 2,
                "name": "string",
                "workflow_id": 2,
                "motion_recommendation_ids": [3],
                "meeting_id": 12,
            },
        },
    )
    finalize("0054_remove_statutes")
    assert_model(
        "motion/1",
        {
            "id": 1,
            "statute_paragraph_id": 1,
            "title": "text",
            "meeting_id": 11,
            "meta_deleted": True,
            "recommendation_id": 1,
            "state_extension_reference_ids": ["motion/2"],
            "referenced_in_motion_state_extension_ids": [2],
            "recommendation_extension_reference_ids": ["motion/2"],
            "referenced_in_motion_recommendation_extension_ids": [2],
            "attachment_ids": [1],
            "block_id": 1,
            "category_id": 1,
            "supporter_meeting_user_ids": [1],
            "tag_ids": [1],
            "comment_ids": [1],
            "editor_ids": [1],
            "personal_note_ids": [1],
            "submitter_ids": [1],
            "poll_ids": [1],
            "option_ids": [1, 2, 3],
            "agenda_item_id": 2,
            "list_of_speakers_id": 1,
        },
    )
    assert_model(
        "motion/3",
        {
            "id": 3,
            "statute_paragraph_id": 3,
            "title": "text",
            "meeting_id": 12,
            "meta_deleted": True,
            "recommendation_id": 2,
        },
    )
    assert_model(
        "meeting/11",
        {
            "id": 11,
            "name": "string",
            "language": "string",
            "motion_workflow_ids": [1],
            "motion_state_ids": [1],
            "mediafile_ids": [1],
            "meeting_user_ids": [1, 2],
            "motion_block_ids": [1],
            "motion_category_ids": [1],
            "motion_comment_section_ids": [1],
            "tag_ids": [1, 2],
            "group_ids": [1],
            "poll_candidate_list_ids": [1],
            "agenda_item_ids": [3],
            "all_projection_ids": [5, 6],
            "projector_ids": [1, 2],
            "topic_ids": [1],
            "point_of_order_category_ids": [1],
            "structure_level_ids": [1],
        },
    )
    assert_model(
        "meeting/12",
        {
            "id": 12,
            "name": "string",
            "language": "string",
            "motion_state_ids": [2],
            "motion_workflow_ids": [2],
        },
    )
    assert_model(
        "motion_statute_paragraph/1",
        {
            "id": 1,
            "title": "string",
            "text": "HTML",
            "meeting_id": 11,
            "motion_ids": [1],
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion_statute_paragraph/2",
        {
            "id": 2,
            "title": "string",
            "text": "HTML",
            "meeting_id": 11,
            "motion_ids": [2],
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion_statute_paragraph/3",
        {
            "id": 3,
            "title": "string",
            "text": "HTML",
            "meeting_id": 12,
            "motion_ids": [3],
            "meta_deleted": True,
        },
    )


def test_migration_full(write, finalize, assert_model):
    create_comprehensive_data(write)
    finalize("0054_remove_statutes")
    assert_model(
        "motion/1",
        {
            "id": 1,
            "statute_paragraph_id": 1,
            "title": "text",
            "recommendation_id": 1,
            "state_extension_reference_ids": ["motion/2"],
            "referenced_in_motion_state_extension_ids": [2],
            "recommendation_extension_reference_ids": ["motion/2"],
            "referenced_in_motion_recommendation_extension_ids": [2],
            "attachment_ids": [1],
            "block_id": 1,
            "category_id": 1,
            "supporter_meeting_user_ids": [1],
            "tag_ids": [1],
            "comment_ids": [1],
            "editor_ids": [1],
            "personal_note_ids": [1],
            "submitter_ids": [1],
            "poll_ids": [1],
            "option_ids": [1, 2, 3],
            "agenda_item_id": 2,
            "list_of_speakers_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion/2",
        {
            "id": 2,
            "statute_paragraph_id": 2,
            "title": "text",
            "recommendation_id": 1,
            "state_extension_reference_ids": ["motion/1"],
            "referenced_in_motion_state_extension_ids": [1],
            "recommendation_extension_reference_ids": ["motion/1"],
            "referenced_in_motion_recommendation_extension_ids": [1],
            "change_recommendation_ids": [1],
            "working_group_speaker_ids": [1],
            "agenda_item_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion_workflow/1",
        {"id": 1, "state_ids": [1], "meeting_id": 11},
    )
    assert_model(
        "meeting/11",
        {
            "id": 11,
            "name": "string",
            "language": "string",
            "motion_workflow_ids": [1],
            "motion_state_ids": [1],
            "mediafile_ids": [1],
            "meeting_user_ids": [1, 2],
            "motion_block_ids": [1],
            "motion_category_ids": [1],
            "motion_comment_section_ids": [1],
            "tag_ids": [1, 2],
            "group_ids": [1],
            "poll_candidate_list_ids": [1],
            "agenda_item_ids": [3],
            "all_projection_ids": [5, 6],
            "projector_ids": [1, 2],
            "topic_ids": [1],
            "point_of_order_category_ids": [1],
            "structure_level_ids": [1],
        },
    )
    assert_model(
        "motion_statute_paragraph/1",
        {
            "id": 1,
            "title": "string",
            "text": "HTML",
            "meeting_id": 11,
            "motion_ids": [1],
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion_statute_paragraph/2",
        {
            "id": 2,
            "title": "string",
            "text": "HTML",
            "meeting_id": 11,
            "motion_ids": [2],
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion_state/1",
        {
            "id": 1,
            "name": "string",
            "workflow_id": 1,
            "meeting_id": 11,
        },
    )
    assert_model(
        "motion_category/1",
        {
            "id": 1,
            "name": "AA",
            "meeting_id": 11,
        },
    )
    assert_model(
        "motion_block/1",
        {"id": 1, "name": "AA", "meeting_id": 11},
    )
    assert_model(
        "meeting_user/1",
        {
            "id": 1,
            "user_id": 1,
            "meeting_id": 11,
        },
    )
    assert_model(
        "meeting_user/2",
        {
            "id": 2,
            "user_id": 2,
            "meeting_id": 11,
        },
    )
    assert_model(
        "user/1",
        {
            "id": 1,
            "meeting_ids": [11],
            # "motion_ids": [1],
            "meeting_user_ids": [1],
        },
    )
    assert_model(
        "user/2",
        {
            "id": 2,
            "meeting_ids": [11],
            # "motion_ids": [1],
            "meeting_user_ids": [2],
        },
    )
    assert_model(
        "tag/1",
        {"id": 1, "name": "A Tag", "meeting_id": 11, "tagged_ids": ["agenda_item/3"]},
    )
    assert_model(
        "tag/2",
        {"id": 2, "name": "A 2nd Tag", "meeting_id": 11},
    )
    assert_model(
        "mediafile/1",
        {
            "id": 1,
            "title": "A Media Attachment",
            "owner_id": "meeting/11",
            "is_public": True,
        },
    )
    assert_model(
        "motion_submitter/1",
        {
            "id": 1,
            "meeting_user_id": 1,
            "motion_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion_editor/1",
        {
            "id": 1,
            "meeting_user_id": 1,
            "motion_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion_working_group_speaker/1",
        {
            "id": 1,
            "meeting_user_id": 1,
            "motion_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion_change_recommendation/1",
        {
            "id": 1,
            "line_from": 1,
            "line_to": 5,
            "text": "HTML",
            "motion_id": 2,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion_comment/1",
        {
            "id": 1,
            "comment": "HTML",
            "motion_id": 1,
            "section_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion_comment_section/1",
        {
            "id": 1,
            "name": "A Comment Section",
            "meeting_id": 11,
        },
    )
    assert_model(
        "projection/1",
        {
            "id": 1,
            "content_object_id": "motion/1",
            "current_projector_id": 1,
            "preview_projector_id": 1,
            "history_projector_id": 2,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "projection/2",
        {
            "id": 2,
            "content_object_id": "poll/1",
            "current_projector_id": 1,
            "history_projector_id": 2,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "projection/3",
        {
            "id": 3,
            "content_object_id": "agenda_item/1",
            "current_projector_id": 1,
            "preview_projector_id": 2,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "projection/4",
        {
            "id": 4,
            "content_object_id": "agenda_item/2",
            "current_projector_id": 2,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "projection/5",
        {
            "id": 5,
            "content_object_id": "agenda_item/3",
            "history_projector_id": 1,
            "meeting_id": 11,
        },
    )
    assert_model(
        "projection/6",
        {
            "id": 6,
            "content_object_id": "topic/1",
            "history_projector_id": 1,
            "meeting_id": 11,
        },
    )
    assert_model(
        "projection/7",
        {
            "id": 7,
            "content_object_id": "list_of_speakers/1",
            "preview_projector_id": 2,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "projector/1",
        {
            "id": 1,
            "history_projection_ids": [5, 6],
            "meeting_id": 11,
        },
    )
    assert_model(
        "projector/2",
        {
            "id": 2,
            "meeting_id": 11,
        },
    )
    assert_model(
        "personal_note/1",
        {
            "id": 1,
            "content_object_id": "motion/1",
            "meeting_user_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "poll/1",
        {
            "id": 1,
            "content_object_id": "motion/1",
            "option_ids": [1, 2, 3],
            "global_option_id": 1,
            "voted_ids": [1],
            "entitled_group_ids": [1],
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "option/1",
        {
            "id": 1,
            "content_object_id": "motion/1",
            "used_as_global_option_in_poll_id": 1,
            "vote_ids": [1],
            "poll_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "option/2",
        {
            "id": 2,
            "content_object_id": "user/1",
            "vote_ids": [],
            "poll_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "option/3",
        {
            "id": 3,
            "content_object_id": "poll_candidate_list/1",
            "vote_ids": [],
            "poll_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "vote/1",
        {
            "id": 1,
            "delegated_user_id": 2,
            "user_id": 1,
            "meeting_id": 11,
            "option_id": 1,
            "meta_deleted": True,
        },
    )
    assert_model(
        "poll_candidate_list/1",
        {
            "id": 1,
            "entries": {"user_id": 1, "weight": 20},
            "meeting_id": 11,
        },
    )
    assert_model(
        "group/1",
        {
            "id": 1,
            "name": "A Group",
            "meeting_id": 11,
        },
    )
    assert_model(
        "agenda_item/1",
        {
            "id": 1,
            "content_object_id": "motion/2",
            "tag_ids": [2],
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "agenda_item/2",
        {
            "id": 2,
            "content_object_id": "motion/1",
            "child_ids": [3],
            "tag_ids": [2],
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "agenda_item/3",
        {
            "id": 3,
            "content_object_id": "topic/1",
            "child_ids": [],
            "tag_ids": [1],
            "projection_ids": [5],
            "meeting_id": 11,
        },
    )
    assert_model(
        "topic/1",
        {
            "id": 1,
            "title": "A tropical topic",
            "agenda_item_id": 3,
            "projection_ids": [6],
            "meeting_id": 11,
        },
    )
    assert_model(
        "list_of_speakers/1",
        {
            "id": 1,
            "content_object_id": "motion/1",
            "speaker_ids": [1],
            "structure_level_list_of_speakers_ids": [1],
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "structure_level_list_of_speakers/1",
        {
            "id": 1,
            "structure_level_id": 1,
            "list_of_speakers_id": 1,
            "initial_time": 30,
            "speaker_ids": [1],
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "structure_level/1",
        {
            "id": 1,
            "name": "ErstePartei",
            "color": "#FF0000",
            "default_time": 30,
            "meeting_id": 11,
        },
    )
    assert_model(
        "speaker/1",
        {
            "id": 1,
            "meeting_user_id": 1,
            "point_of_order_category_id": 1,
            "list_of_speakers_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "point_of_order_category/1",
        {
            "id": 1,
            "text": "A point of order category",
            "rank": 1,
            "meeting_id": 11,
        },
    )


def test_non_deleted_motion_extension(write, finalize, assert_model):
    """This tests if the fields state_extension_reference_ids and recommendation_extension_reference_ids are correctly processed and the corresponding motions updated"""
    create_comprehensive_data(write)
    write(
        {
            "type": "update",
            "fqid": "motion/2",
            "fields": {
                "state_extension_reference_ids": ["motion/1", "motion/3"],
                "recommendation_extension_reference_ids": ["motion/1", "motion/3"],
            },
        },
        {"type": "update", "fqid": "meeting/11", "fields": {"motion_ids": [1, 2, 3]}},
        {
            "type": "update",
            "fqid": "motion_state/1",
            "fields": {"motion_recommendation_ids": [1, 2, 3]},
        },
        {
            "type": "create",
            "fqid": "motion/3",
            "fields": {
                "id": 3,
                "title": "text",
                "meeting_id": 11,
                "recommendation_id": 1,
                "referenced_in_motion_state_extension_ids": [2],
                "referenced_in_motion_recommendation_extension_ids": [2],
            },
        },
    )
    finalize("0054_remove_statutes")
    assert_model(
        "motion/3",
        {
            "id": 3,
            "title": "text",
            "meeting_id": 11,
            "recommendation_id": 1,
        },
    )
    assert_model(
        "motion/2",
        {
            "id": 2,
            "statute_paragraph_id": 2,
            "title": "text",
            "recommendation_id": 1,
            "state_extension_reference_ids": ["motion/1", "motion/3"],
            "referenced_in_motion_state_extension_ids": [1],
            "recommendation_extension_reference_ids": ["motion/1", "motion/3"],
            "referenced_in_motion_recommendation_extension_ids": [1],
            "change_recommendation_ids": [1],
            "working_group_speaker_ids": [1],
            "agenda_item_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )

    # assert models updated and backrelation emtied including workflow and motion
