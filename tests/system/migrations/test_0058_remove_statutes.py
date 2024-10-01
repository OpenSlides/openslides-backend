def write_comprehensive_data(write) -> dict:
    data = {
        "meeting/11": {
            "id": 11,
            "name": "string",
            "language": "string",
            "motions_statutes_enabled": True,
            "motions_statute_recommendations_by": 12,
            "motion_statute_paragraph_ids": [1, 2],
            "motions_default_statute_amendment_workflow_id": 1,
            "motion_ids": [1, 2],
            "motion_workflow_ids": [1],
            "motion_state_ids": [1],
            "motion_category_ids": [1],
            "motion_block_ids": [1],
            "meeting_user_ids": [1, 2],
            "tag_ids": [1, 2],
            "mediafile_ids": [1],
            "meeting_mediafile_ids": [1],
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
            "option_ids": [1, 2, 3],
            "poll_ids": [1],
            "agenda_item_ids": [1, 2, 3],
            "topic_ids": [1],
            "structure_level_list_of_speakers_ids": [1],
            "list_of_speakers_ids": [1],
            "structure_level_ids": [1],
            "speaker_ids": [1],
            "point_of_order_category_ids": [1],
        },
        "motion/1": {
            "id": 1,
            "statute_paragraph_id": 1,
            "title": "text",
            "recommendation_id": 1,
            "amendment_ids": [666],
            "state_extension_reference_ids": ["motion/2"],
            "referenced_in_motion_state_extension_ids": [2],
            "recommendation_extension_reference_ids": ["motion/2"],
            "referenced_in_motion_recommendation_extension_ids": [2],
            "category_id": 1,
            "block_id": 1,
            "supporter_meeting_user_ids": [1],
            "tag_ids": [1, 2],
            "attachment_meeting_mediafile_ids": [1],
            "working_group_speaker_ids": [1],
            "submitter_ids": [1],
            "editor_ids": [1],
            "comment_ids": [1],
            "projection_ids": [1],
            "personal_note_ids": [1],
            "option_ids": [1],
            "poll_ids": [1],
            "agenda_item_id": 2,
            "list_of_speakers_id": 1,
            "meeting_id": 11,
        },
        "motion/2": {
            "id": 2,
            "statute_paragraph_id": 2,
            "title": "text",
            "meeting_id": 11,
            "recommendation_id": 1,
            "state_extension_reference_ids": ["motion/1"],
            "referenced_in_motion_state_extension_ids": [1],
            "recommendation_extension_reference_ids": ["motion/1"],
            "referenced_in_motion_recommendation_extension_ids": [1],
            "change_recommendation_ids": [1],
            "agenda_item_id": 1,
        },
        "motion/666": {"id": 666, "lead_motion_id": 1},
        "motion_category/1": {
            "id": 1,
            "name": "AA",
            "meeting_id": 11,
            "motion_ids": [1],
        },
        "motion_block/1": {
            "id": 1,
            "name": "AA",
            "meeting_id": 11,
            "motion_ids": [1],
        },
        "meeting_user/1": {
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
        "meeting_user/2": {
            "id": 2,
            "user_id": 2,
            "meeting_id": 11,
        },
        "user/1": {
            "id": 1,
            "meeting_ids": [11],
            "meeting_user_ids": [1],
            "poll_voted_ids": [1],
            "vote_ids": [1],
            "option_ids": [2],
        },
        "user/2": {
            "id": 2,
            "meeting_ids": [11],
            "meeting_user_ids": [2],
            "delegated_vote_ids": [1],
        },
        "tag/1": {
            "id": 1,
            "name": "A Tag",
            "meeting_id": 11,
            "tagged_ids": ["motion/1", "agenda_item/3"],
        },
        "tag/2": {
            "id": 2,
            "name": "A 2nd Tag",
            "meeting_id": 11,
            "tagged_ids": ["motion/1", "agenda_item/1", "agenda_item/2"],
        },
        "meeting_mediafile/1": {
            "id": 1,
            "attachment_ids": ["motion/1"],
            "mediafile_id": 1,
            "is_public": True,
            "meeting_id": 11,
        },
        "mediafile/1": {
            "id": 1,
            "title": "A Media Attachment",
            "owner_id": "meeting/11",
            "is_public": True,
            "meeting_mediafile_ids": [1],
        },
        "motion_submitter/1": {
            "id": 1,
            "meeting_user_id": 1,
            "motion_id": 1,
            "meeting_id": 11,
        },
        "motion_editor/1": {
            "id": 1,
            "meeting_user_id": 1,
            "motion_id": 1,
            "meeting_id": 11,
        },
        "motion_working_group_speaker/1": {
            "id": 1,
            "meeting_user_id": 1,
            "motion_id": 1,
            "meeting_id": 11,
        },
        "motion_change_recommendation/1": {
            "id": 1,
            "line_from": 1,
            "line_to": 5,
            "text": "HTML",
            "motion_id": 2,
            "meeting_id": 11,
        },
        "motion_comment/1": {
            "id": 1,
            "comment": "HTML",
            "motion_id": 1,
            "section_id": 1,
            "meeting_id": 11,
        },
        "motion_comment_section/1": {
            "id": 1,
            "name": "A Comment Section",
            "comment_ids": [1],
            "meeting_id": 11,
        },
        "projection/1": {
            "id": 1,
            "content_object_id": "motion/1",
            "current_projector_id": 1,
            "preview_projector_id": 1,
            "history_projector_id": 2,
            "meeting_id": 11,
        },
        "projection/2": {
            "id": 2,
            "content_object_id": "poll/1",
            "current_projector_id": 1,
            "history_projector_id": 2,
            "meeting_id": 11,
        },
        "projection/3": {
            "id": 3,
            "content_object_id": "agenda_item/1",
            "current_projector_id": 1,
            "preview_projector_id": 2,
            "meeting_id": 11,
        },
        "projection/4": {
            "id": 4,
            "content_object_id": "agenda_item/2",
            "current_projector_id": 2,
            "meeting_id": 11,
        },
        "projection/5": {
            "id": 5,
            "content_object_id": "agenda_item/3",
            "history_projector_id": 1,
            "meeting_id": 11,
        },
        "projection/6": {
            "id": 6,
            "content_object_id": "topic/1",
            "history_projector_id": 1,
            "meeting_id": 11,
        },
        "projection/7": {
            "id": 7,
            "content_object_id": "list_of_speakers/1",
            "preview_projector_id": 2,
            "meeting_id": 11,
        },
        "projector/1": {
            "id": 1,
            "current_projection_ids": [1, 2, 3],
            "preview_projection_ids": [1],
            "history_projection_ids": [5, 6],
            "meeting_id": 11,
        },
        "projector/2": {
            "id": 2,
            "current_projection_ids": [4],
            "preview_projection_ids": [3, 7],
            "history_projection_ids": [1, 2],
            "meeting_id": 11,
        },
        "personal_note/1": {
            "id": 1,
            "meeting_user_id": 1,
            "content_object_id": "motion/1",
            "meeting_id": 11,
        },
        "poll/1": {
            "id": 1,
            "content_object_id": "motion/1",
            "option_ids": [1, 2, 3],
            "global_option_id": 1,
            "voted_ids": [1],
            "entitled_group_ids": [1],
            "projection_ids": [2],
            "meeting_id": 11,
        },
        "option/1": {
            "id": 1,
            "content_object_id": "motion/1",
            "used_as_global_option_in_poll_id": 1,
            "vote_ids": [1],
            "poll_id": 1,
            "meeting_id": 11,
        },
        "option/2": {
            "id": 2,
            "content_object_id": "user/1",
            "vote_ids": [],
            "poll_id": 1,
            "meeting_id": 11,
        },
        "option/3": {
            "id": 3,
            "content_object_id": "poll_candidate_list/1",
            "vote_ids": [],
            "poll_id": 1,
            "meeting_id": 11,
        },
        "vote/1": {
            "id": 1,
            "delegated_user_id": 2,
            "user_id": 1,
            "meeting_id": 11,
            "option_id": 1,
        },
        "poll_candidate_list/1": {
            "id": 1,
            "option_id": 3,
            "entries": {"user_id": 1, "weight": 20},
            "meeting_id": 11,
        },
        "group/1": {
            "id": 1,
            "poll_ids": [1],
            "name": "A Group",
            "meeting_id": 11,
        },
        "agenda_item/1": {
            "id": 1,
            "content_object_id": "motion/2",
            "parent_id": None,
            "child_ids": [2],
            "tag_ids": [2],
            "projection_ids": [3],
            "meeting_id": 11,
        },
        "agenda_item/2": {
            "id": 2,
            "content_object_id": "motion/1",
            "parent_id": 1,
            "child_ids": [3],
            "tag_ids": [2],
            "projection_ids": [4],
            "meeting_id": 11,
        },
        "agenda_item/3": {
            "id": 3,
            "content_object_id": "topic/1",
            "parent_id": 2,
            "child_ids": [],
            "tag_ids": [1],
            "projection_ids": [5],
            "meeting_id": 11,
        },
        "topic/1": {
            "id": 1,
            "title": "A tropical topic",
            "agenda_item_id": 3,
            "projection_ids": [6],
            "meeting_id": 11,
        },
        "list_of_speakers/1": {
            "id": 1,
            "content_object_id": "motion/1",
            "speaker_ids": [1],
            "structure_level_list_of_speakers_ids": [1],
            "projection_ids": [7],
            "meeting_id": 11,
        },
        "structure_level_list_of_speakers/1": {
            "id": 1,
            "structure_level_id": 1,
            "list_of_speakers_id": 1,
            "initial_time": 30,
            "speaker_ids": [1],
            "meeting_id": 11,
        },
        "structure_level/1": {
            "id": 1,
            "name": "ErstePartei",
            "color": "#FF0000",
            "default_time": 30,
            "structure_level_list_of_speakers_ids": [1],
            "meeting_id": 11,
        },
        "speaker/1": {
            "id": 1,
            "meeting_user_id": 1,
            "point_of_order_category_id": 1,
            "list_of_speakers_id": 1,
            "structure_level_list_of_speakers_id": 1,
            "meeting_id": 11,
        },
        "point_of_order_category/1": {
            "id": 1,
            "text": "A point of order category",
            "speaker_ids": [1],
            "rank": 1,
            "meeting_id": 11,
        },
        "motion_workflow/1": {
            "id": 1,
            "default_statute_amendment_workflow_meeting_id": 11,
            "state_ids": [1],
            "meeting_id": 11,
        },
        "motion_statute_paragraph/1": {
            "id": 1,
            "title": "string",
            "text": "HTML",
            "meeting_id": 11,
            "motion_ids": [1],
        },
        "motion_statute_paragraph/2": {
            "id": 2,
            "title": "string",
            "text": "HTML",
            "meeting_id": 11,
            "motion_ids": [2],
        },
        "motion_state/1": {
            "id": 1,
            "name": "string",
            "workflow_id": 1,
            "motion_recommendation_ids": [1, 2],
            "meeting_id": 11,
        },
    }
    write(
        *[
            {
                "type": "create",
                "fqid": fqid,
                "fields": fields,
            }
            for fqid, fields in data.items()
        ]
    )
    return data


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
    finalize("0058_remove_statutes")
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
    finalize("0058_remove_statutes")
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


def test_no_sideffects_submodels(write, finalize, assert_model):
    write_comprehensive_data(write)
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
            "attachment_meeting_mediafile_ids": [2],
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
        "meeting_mediafile/2": {
            "id": 2,
            "mediafile_id": 2,
            "attachment_ids": ["motion/3"],
            "is_public": True,
            "meeting_id": 11,
        },
        "mediafile/2": {
            "id": 2,
            "title": "A Media Attachment",
            "owner_id": "meeting/11",
            "is_public": True,
            "meeting_mediafile_ids": [2],
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
                "meeting_mediafile_ids": [1, 2],
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
                "poll_voted_ids": [1, 2],
                "vote_ids": [1, 2],
                "option_ids": [2, 12],
            },
        },
        {
            "type": "update",
            "fqid": "user/2",
            "fields": {
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
                    "agenda_item/2",
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
    finalize("0058_remove_statutes")
    assert_model(
        "motion/1",
        {
            "id": 1,
            "statute_paragraph_id": 1,
            "title": "text",
            "amendment_ids": [666],
            "agenda_item_id": 2,
            "attachment_meeting_mediafile_ids": [1],
            "block_id": 1,
            "category_id": 1,
            "comment_ids": [1],
            "working_group_speaker_ids": [1],
            "editor_ids": [1],
            "list_of_speakers_id": 1,
            "option_ids": [1],
            "personal_note_ids": [1],
            "poll_ids": [1],
            "recommendation_extension_reference_ids": ["motion/2"],
            "recommendation_id": 1,
            "referenced_in_motion_recommendation_extension_ids": [2],
            "referenced_in_motion_state_extension_ids": [2],
            "state_extension_reference_ids": ["motion/2"],
            "submitter_ids": [1],
            "supporter_meeting_user_ids": [1],
            "tag_ids": [1, 2],
            "meeting_id": 11,
            "projection_ids": [1],
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
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
    assert_model(
        "tag/2",
        {
            "id": 2,
            "name": "A 2nd Tag",
            "meeting_id": 11,
            "tagged_ids": ["agenda_item/11", "agenda_item/12"],
        },
    )
    for fqid, fields in data.items():
        assert_model(fqid, fields)


def test_two_meetings(write, finalize, assert_model):
    write_comprehensive_data(write)
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
                "motions_default_statute_amendment_workflow_id": 2,
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
    finalize("0058_remove_statutes")
    assert_model(
        "motion/1",
        {
            "id": 1,
            "statute_paragraph_id": 1,
            "title": "text",
            "meeting_id": 11,
            "recommendation_id": 1,
            "amendment_ids": [666],
            "state_extension_reference_ids": ["motion/2"],
            "referenced_in_motion_state_extension_ids": [2],
            "recommendation_extension_reference_ids": ["motion/2"],
            "referenced_in_motion_recommendation_extension_ids": [2],
            "attachment_meeting_mediafile_ids": [1],
            "block_id": 1,
            "category_id": 1,
            "supporter_meeting_user_ids": [1],
            "tag_ids": [1, 2],
            "comment_ids": [1],
            "working_group_speaker_ids": [1],
            "editor_ids": [1],
            "personal_note_ids": [1],
            "submitter_ids": [1],
            "poll_ids": [1],
            "option_ids": [1],
            "agenda_item_id": 2,
            "list_of_speakers_id": 1,
            "projection_ids": [1],
            "meta_deleted": True,
        },
    )
    assert_model(
        "motion/3",
        {
            "id": 3,
            "statute_paragraph_id": 3,
            "title": "text",
            "meeting_id": 12,
            "recommendation_id": 2,
            "meta_deleted": True,
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
            "meeting_mediafile_ids": [1],
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
    assert_model(
        "motion_workflow/2",
        {
            "id": 2,
            "state_ids": [2],
            "meeting_id": 12,
        },
    )


def test_migration_full(write, finalize, assert_model):
    data = write_comprehensive_data(write)
    finalize("0058_remove_statutes")
    data_update = {
        "meeting/11": {
            "motion_statute_paragraph_ids": None,
            "motions_statutes_enabled": None,
            "motions_statute_recommendations_by": None,
            "motions_default_statute_amendment_workflow_id": None,
            "agenda_item_ids": [3],
            "all_projection_ids": [5, 6],
            "motion_change_recommendation_ids": None,
            "motion_comment_ids": None,
            "motion_editor_ids": None,
            "motion_ids": None,
            "motion_submitter_ids": None,
            "list_of_speakers_ids": None,
            "structure_level_list_of_speakers_ids": None,
            "vote_ids": None,
            "speaker_ids": None,
            "poll_ids": None,
            "personal_note_ids": None,
            "option_ids": None,
            "motion_working_group_speaker_ids": None,
        },
        "motion/1": {
            "meta_deleted": True,
        },
        "motion/2": {
            "meta_deleted": True,
        },
        "motion/666": {
            "meta_deleted": True,
        },
        "motion_category/1": {"motion_ids": None},
        "motion_block/1": {"motion_ids": None},
        "meeting_user/1": {
            "motion_editor_ids": None,
            "motion_submitter_ids": None,
            "motion_working_group_speaker_ids": None,
            "personal_note_ids": None,
            "speaker_ids": None,
            "supported_motion_ids": None,
        },
        "meeting_user/2": {
            "motion_editor_ids": None,
            "motion_submitter_ids": None,
            "motion_working_group_speaker_ids": None,
            "personal_note_ids": None,
            "speaker_ids": None,
            "supported_motion_ids": None,
        },
        "user/1": {
            "motion_ids": None,
            "option_ids": None,
            "poll_voted_ids": None,
            "vote_ids": None,
        },
        "user/2": {
            "motion_ids": None,
            "delegated_vote_ids": None,
        },
        "tag/1": {"tagged_ids": ["agenda_item/3"]},
        "tag/2": {"tagged_ids": None},
        "meeting_mediafile/1": {"attachment_ids": None},
        "motion_submitter/1": {
            "meta_deleted": True,
        },
        "motion_editor/1": {
            "meta_deleted": True,
        },
        "motion_working_group_speaker/1": {
            "meta_deleted": True,
        },
        "motion_change_recommendation/1": {
            "meta_deleted": True,
        },
        "motion_statute_paragraph/1": {
            "meta_deleted": True,
        },
        "motion_statute_paragraph/2": {
            "meta_deleted": True,
        },
        "motion_comment/1": {
            "meta_deleted": True,
        },
        "motion_comment_section/1": {"comment_ids": None},
        "projection/1": {
            "meta_deleted": True,
        },
        "projection/2": {
            "meta_deleted": True,
        },
        "projection/3": {
            "meta_deleted": True,
        },
        "projection/4": {
            "meta_deleted": True,
        },
        "projection/7": {
            "meta_deleted": True,
        },
        "projector/1": {
            "preview_projection_ids": None,
            "current_projection_ids": None,
        },
        "projector/2": {
            "preview_projection_ids": None,
            "current_projection_ids": None,
            "history_projection_ids": None,
        },
        "personal_note/1": {
            "meta_deleted": True,
        },
        "poll/1": {
            "meta_deleted": True,
        },
        "option/1": {
            "meta_deleted": True,
        },
        "option/2": {
            "meta_deleted": True,
        },
        "option/3": {
            "meta_deleted": True,
        },
        "vote/1": {
            "meta_deleted": True,
        },
        "poll_candidate_list/1": {"option_id": None},
        "group/1": {"poll_ids": None},
        "agenda_item/1": {
            "meta_deleted": True,
        },
        "agenda_item/2": {
            "meta_deleted": True,
        },
        "agenda_item/3": {
            "parent_id": None,
        },
        "list_of_speakers/1": {
            "meta_deleted": True,
        },
        "structure_level_list_of_speakers/1": {
            "meta_deleted": True,
        },
        "structure_level/1": {
            "structure_level_list_of_speakers_ids": None,
        },
        "speaker/1": {
            "meta_deleted": True,
        },
        "point_of_order_category/1": {
            "speaker_ids": None,
        },
        "motion_workflow/1": {"default_statute_amendment_workflow_meeting_id": None},
        "motion_state/1": {
            "motion_recommendation_ids": None,
        },
    }
    for fqid, fields in data_update.items():
        data_fields = data.get(fqid)
        data_fields.update(fields)
        for key, value in fields.items():
            if value is None:
                del data_fields[key]
    for fqid, fields in data.items():
        assert_model(fqid, fields)


def test_non_deleted_motion_extension(write, finalize, assert_model):
    """
    Tests if the fields state_extension_reference_ids and recommendation_extension_reference_ids
    are correctly processed and the corresponding motions updated.
    """
    write_comprehensive_data(write)
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
    finalize("0058_remove_statutes")
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
            "agenda_item_id": 1,
            "meeting_id": 11,
            "meta_deleted": True,
        },
    )
