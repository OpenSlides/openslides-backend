def prepare_actions_map() -> None:
    """
    This function just imports all action modules so that the actions are
    recognized by the system and the register decorator can do its work.

    New modules have to be added here.
    """
    from . import (  # noqa
        agenda_item,
        assignment,
        assignment_candidate,
        chat_group,
        chat_message,
        committee,
        gender,
        group,
        history_entry,
        history_position,
        list_of_speakers,
        mediafile,
        meeting,
        meeting_mediafile,
        meeting_user,
        motion,
        motion_block,
        motion_category,
        motion_change_recommendation,
        motion_comment,
        motion_comment_section,
        motion_editor,
        motion_state,
        motion_submitter,
        motion_supporter,
        motion_workflow,
        motion_working_group_speaker,
        option,
        organization,
        organization_tag,
        personal_note,
        point_of_order_category,
        poll,
        poll_candidate,
        poll_candidate_list,
        projection,
        projector,
        projector_countdown,
        projector_message,
        speaker,
        structure_level,
        structure_level_list_of_speakers,
        tag,
        theme,
        topic,
        user,
        vote,
    )


prepare_actions_map()
