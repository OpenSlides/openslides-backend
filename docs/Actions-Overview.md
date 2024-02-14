A more general format description see in [Action-Service](https://github.com/OpenSlides/OpenSlides/wiki/Action-Service)
## Organization and committees

- [committee.create](actions/committee.create)
- [committee.delete](actions/committee.delete)
- [committee.update](actions/committee.update)
- [committee.json_upload](actions/committee.json_upload)
- [committee.import](actions/committee.import)
- [organization.update](actions/organization.update)
- [organization.initial_import](actions/organization.initial_import)
- [organization.delete_history_information](actions/organization.delete_history_information)

## Agenda item

- [agenda_item.assign](actions/agenda_item.assign)
- [agenda_item.create](actions/agenda_item.create)
- [agenda_item.delete](actions/agenda_item.delete)
- [agenda_item.numbering](actions/agenda_item.numbering)
- [agenda_item.sort](actions/agenda_item.sort)
- [agenda_item.update](actions/agenda_item.update)

## Assignments

- [assignment.create](actions/assignment.create)
- [assignment.delete](actions/assignment.delete)
- [assignment.update](actions/assignment.update)
- [assignment_candidate.create](actions/assignment_candidate.create)
- [assignment_candidate.delete](actions/assignment_candidate.delete)
- [assignment_candidate.sort](actions/assignment_candidate.sort)

## Chat groups

- [chat_group.clear](actions/chat_group.clear)
- [chat_group.create](actions/chat_group.create)
- [chat_group.delete](actions/chat_group.delete)
- [chat_group.sort](actions/chat_group.sort)
- [chat_group.update](actions/chat_group.update)

## Chat messages

- [chat_message.create](actions/chat_message.create)
- [chat_message.delete](actions/chat_message.delete)
- [chat_message.update](actions/chat_message.update)

## Groups

- [group.create](actions/group.create)
- [group.delete](actions/group.delete)
- [group.update](actions/group.update)

## List of speakers (LOS)

- [list_of_speakers.delete_all_speakers](actions/list_of_speakers.delete_all_speakers)
- [list_of_speakers.re_add_last](actions/list_of_speakers.re_add_last)
- [list_of_speakers.update](actions/list_of_speakers.update)

## Mediafiles

- [mediafile.create_directory](actions/mediafile.create_directory)
- [mediafile.delete](actions/mediafile.delete)
- [mediafile.move](actions/mediafile.move)
- [mediafile.update](actions/mediafile.update)
- [mediafile.upload](actions/mediafile.upload)

## Meetings

- [meeting.clone](actions/meeting.clone)
- [meeting.create_from_template](actions/meeting.create_from_template)
- [meeting.create](actions/meeting.create)
- [meeting.delete](actions/meeting.delete)
- [meeting.import](actions/meeting.import)
- [meeting.delete_all_speakers_of_all_lists](actions/meeting.delete_all_speakers_of_all_lists)
- [meeting.set_font](actions/meeting.set_font)
- [meeting.set_logo](actions/meeting.set_logo)
- [meeting.update](actions/meeting.update)
- [meeting.unset_font](actions/meeting.unset_font)
- [meeting.unset_logo](actions/meeting.unset_logo)
- [meeting.archive](actions/meeting.archive)
- [meeting.unarchive](actions/meeting.unarchive)

## Motions

- [motion.create](actions/motion.create)
- [motion.create_forwarded](actions/motion.create_forwarded)
- [motion.delete](actions/motion.delete)
- [motion.update](actions/motion.update)
- [motion.sort](actions/motion.sort)
- [motion.follow_recommendation](actions/motion.follow_recommendation)
- [motion.set_recommendation](actions/motion.set_recommendation)
- [motion.reset_recommendation](actions/motion.reset_recommendation)
- [motion.set_support_self](actions/motion.set_support_self)
- [motion.set_state](actions/motion.set_state)
- [motion.reset_state](actions/motion.reset_state)

## Motion related objects

- [motion_block.create](actions/motion_block.create)
- [motion_block.delete](actions/motion_block.delete)
- [motion_block.update](actions/motion_block.update)
- [motion_category.create](actions/motion_category.create)
- [motion_category.delete](actions/motion_category.delete)
- [motion_category.number_motions](actions/motion_category.number_motions)
- [motion_category.sort_motions_in_category](actions/motion_category.sort_motions_in_category)
- [motion_category.sort](actions/motion_category.sort)
- [motion_category.update](actions/motion_category.update)
- [motion_change_recommendation.create](actions/motion_change_recommendation.create)
- [motion_change_recommendation.delete](actions/motion_change_recommendation.delete)
- [motion_change_recommendation.update](actions/motion_change_recommendation.update)
- [motion_comment.create](actions/motion_comment.create)
- [motion_comment.delete](actions/motion_comment.delete)
- [motion_comment.update](actions/motion_comment.update)
- [motion_comment_section.create](actions/motion_comment_section.create)
- [motion_comment_section.delete](actions/motion_comment_section.delete)
- [motion_comment_section.sort](actions/motion_comment_section.sort)
- [motion_comment_section.update](actions/motion_comment_section.update)
- [motion_statute_paragraph.create](actions/motion_statute_paragraph.create)
- [motion_statute_paragraph.delete](actions/motion_statute_paragraph.delete)
- [motion_statute_paragraph.sort](actions/motion_statute_paragraph.sort)
- [motion_statute_paragraph.update](actions/motion_statute_paragraph.update)
- [motion_submitter.create](actions/motion_submitter.create)
- [motion_submitter.delete](actions/motion_submitter.delete)
- [motion_submitter.sort](actions/motion_submitter.sort)

## Motion workflows and states

- [motion_workflow.create](actions/motion_workflow.create)
- [motion_workflow.delete](actions/motion_workflow.delete)
- [motion_workflow.update](actions/motion_workflow.update)
- [motion_workflow.import](actions/motion_workflow.import)
- [motion_state.create](actions/motion_state.create)
- [motion_state.delete](actions/motion_state.delete)
- [motion_state.sort](actions/motion_state.sort)
- [motion_state.update](actions/motion_state.update)

## Organization Tags

- [organization_tag.create](actions/organization_tag.create)
- [organization_tag.delete](actions/organization_tag.delete)
- [organization_tag.update](actions/organization_tag.update)

## Personal notes

- [personal_note.create](actions/personal_note.create)
- [personal_note.delete](actions/personal_note.delete)
- [personal_note.update](actions/personal_note.update)

## Projector and Projection
- [projector.create](projection#projectorcreate)
- [projector.update](projection#projectorupdate)
- [projector.delete](projection#projectordelete)
- [projector.control_view](projection#projectorcontrol_view)
- [projector.project](projection#project-something-projectorproject)
- [projector.toggle](projection#toggle-projections-projectortoggle)
- [projection.update_options](projection#change-projection-options-projectionupdate_options)
- [projection.delete](projection#unproject-without-history-projectiondelete)
- [projector.next](projection#projectornext)
- [projector.previous](projection#projectorprevious)
- [projector.add_to_preview](projection#projectoradd_to_preview)
- [projector.project_preview](projection#projectorproject_preview)
- [projector.sort_preview](projection#projectorsort_preview)

## Projector content objects

- [projector_countdown.create](actions/projector_countdown.create)
- [projector_countdown.delete](actions/projector_countdown.delete)
- [projector_countdown.update](actions/projector_countdown.update)
- [projector_message.create](actions/projector_message.create)
- [projector_message.delete](actions/projector_message.delete)
- [projector_message.update](actions/projector_message.update)

## Point of order categories

- [point_of_order_category.create](actions/point_of_order_category.create)
- [point_of_order_category.delete](actions/point_of_order_category.delete)
- [point_of_order_category.update](actions/point_of_order_category.update)

## Speaker

- [speaker.create](actions/speaker.create)
- [speaker.delete](actions/speaker.delete)
- [speaker.end_speech](actions/speaker.end_speech)
- [speaker.pause](actions/speaker.pause)
- [speaker.speak](actions/speaker.speak)
- [speaker.sort](actions/speaker.sort)
- [speaker.unpause](actions/speaker.unpause)
- [speaker.update](actions/speaker.update)

## Structure level

- [structure_level.create](actions/structure_level.create)
- [structure_level.delete](actions/structure_level.delete)
- [structure_level.update](actions/structure_level.update)
- [structure_level_list_of_speakers.add_time](actions/structure_level_list_of_speakers.add_time)
- [structure_level_list_of_speakers.create](actions/structure_level_list_of_speakers.create)
- [structure_level_list_of_speakers.update](actions/structure_level_list_of_speakers.update)
- [structure_level_list_of_speakers.delete](actions/structure_level_list_of_speakers.delete)

## Tags

- [tag.create](actions/tag.create)
- [tag.delete](actions/tag.delete)
- [tag.update](actions/tag.update)

## Themes

- [theme.create](actions/theme.create)
- [theme.delete](actions/theme.delete)
- [theme.update](actions/theme.update)

## Topics

- [topic.create](actions/topic.create)
- [topic.delete](actions/topic.delete)
- [topic.update](actions/topic.update)
- [topic.json_upload](actions/topic.json_upload)
- [topic.import](actions/topic.import)

## Users
- [user.assign_meetings](actions/user.assign_meetings)
- [user.create](actions/user.create)
- [user.delete](actions/user.delete)
- [user.forget_password](actions/user.forget_password)
- [user.forget_password_confirm](actions/user.forget_password_confirm)
- [user.generate_new_password](actions/user.generate_new_password)
- [user.merge_together](actions/user.merge_together)
- [user.reset_password_to_default](actions/user.reset_password_to_default)
- [user.send_invitation_email](actions/user.send_invitation_email)
- [user.set_password](actions/user.set_password)
- [user.set_password_self](actions/user.set_password_self)
- [user.set_present](actions/user.set_present)
- [user.toggle_presence_by_number](actions/user.toggle_presence_by_number)
- [user.update](actions/user.update)
- [user.update_self](actions/user.update_self)
- [user.save_saml_account](actions/user.save_saml_account)
- [meeting_user.create](actions/meeting_user.create)
- [meeting_user.update](actions/meeting_user.update)
- [meeting_user.delete](actions/meeting_user.delete)
- [account.json_upload](actions/account.json_upload)
- [account.import](actions/account.import)
- [participant.json_upload](actions/participant.json_upload)
- [participant.import](actions/participant.import)

## Voting

- [option.update](actions/option.update)
- [poll.create](actions/poll.create)
- [poll.delete](actions/poll.delete)
- [poll.update](actions/poll.update)
- [poll.start](actions/poll.start)
- [poll.stop](actions/poll.stop)
- [poll.publish](actions/poll.publish)
- [poll.reset](actions/poll.reset)
- [poll.anonymize](actions/poll.anonymize)
- [poll.vote](actions/poll.vote)
- [poll_candidate_list.create](actions/poll_candidate_list.create)
- [poll_candidate_list.delete](actions/poll_candidate_list.delete)
- [poll_candidate.create](actions/poll_candidate.create)
- [poll_candidate.delete](actions/poll_candidate.delete)

