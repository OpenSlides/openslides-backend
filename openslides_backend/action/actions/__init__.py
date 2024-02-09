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
        group,
        list_of_speakers,
        mediafile,
        meeting,
        meeting_user,
        motion,
        motion_block,
        motion_category,
        motion_change_recommendation,
        motion_comment,
        motion_comment_section,
        motion_state,
        motion_statute_paragraph,
        motion_submitter,
        motion_workflow,
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
        tag,
        theme,
        topic,
        user,
        vote,
    )


prepare_actions_map()
