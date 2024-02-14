### Includes changes of feature branch `los-extension`!

## Payload
```js
{
// Required
    id: Id;
    
// Optional
// Group A
    welcome_title: string;
    welcome_text: HTMLPermissive;

    name: string;
    description: string;
    location: string;
    start_time: timestamp;
    end_time: timestamp;

    conference_show: boolean;
    conference_auto_connect: boolean;
    conference_los_restriction: boolean;
    conference_stream_url: string;
    conference_stream_poster_url: string;
    conference_open_microphone: boolean;
    conference_open_video: boolean;
    conference_auto_connect_next_speakers: number;
    conference_enable_helpdesk: boolean;

    applause_enable: boolean;
    applause_type: string;
    applause_show_level: boolean;
    applause_min_amount: number;
    applause_max_amount: number;
    applause_timeout: number;
    applause_particle_image_url: string;

    projector_countdown_default_time: number;
    projector_countdown_warning_time: number;

    export_csv_encoding: string;
    export_csv_separator: string;
    export_pdf_pagenumber_alignment: string;
    export_pdf_fontsize: number;
    export_pdf_pagesize: string;

    agenda_show_subtitles: boolean;
    agenda_enable_numbering: boolean;
    agenda_number_prefix: string;
    agenda_numeral_system: string;
    agenda_item_creation: string;
    agenda_new_items_default_visibility: string;
    agenda_show_internal_items_on_projector: boolean;

    list_of_speakers_amount_last_on_projector: number;
    list_of_speakers_amount_next_on_projector: number;
    list_of_speakers_couple_countdown: boolean;
    list_of_speakers_show_amount_of_speakers_on_slide: boolean;
    list_of_speakers_present_users_only: boolean;
    list_of_speakers_show_first_contribution: boolean;
    list_of_speakers_enable_point_of_order_speakers: boolean;
    list_of_speakers_enable_point_of_order_categories: boolean;
    list_of_speakers_closing_disables_point_of_order: boolean;
    list_of_speakers_enable_pro_contra_speech: boolean;
    list_of_speakers_can_set_contribution_self: boolean;
    list_of_speakers_speaker_note_for_everyone: boolean;
    list_of_speakers_initially_closed: boolean;
    list_of_speakers_default_structure_level_time: number;
    list_of_speakers_enable_interposed_question: boolean;
    list_of_speakers_intervention_time: number;

    motions_default_workflow_id: Id;
    motions_default_amendment_workflow_id: Id;
    motions_default_statute_amendment_workflow_id: Id;
    motions_preamble: string;
    motions_default_line_numbering: string;
    motions_line_length: number;
    motions_reason_required: boolean;
    motions_enable_text_on_projector: boolean;
    motions_enable_reason_on_projector: boolean;
    motions_enable_sidebox_on_projector: boolean;
    motions_enable_recommendation_on_projector: boolean;
    motions_show_referring_motions: boolean;
    motions_show_sequential_number: boolean;
    motions_recommendations_by: string;
    motions_block_slide_columns: number;
    motions_statute_recommendations_by: string;
    motions_recommendation_text_mode: string;
    motions_default_sorting: string;
    motions_number_type: string;
    motions_number_min_digits: number;
    motions_number_with_blank: boolean;
    motions_statutes_enabled: boolean;
    motions_amendments_enabled: boolean;
    motions_amendments_in_main_list: boolean;
    motions_amendments_of_amendments: boolean;
    motions_amendments_prefix: string;
    motions_amendments_text_mode: string;
    motions_amendments_multiple_paragraphs: boolean;
    motions_supporters_min_amount: number;
    motions_export_title: string;
    motions_export_preamble: string;
    motions_export_submitter_recommendation: boolean;
    motions_export_follow_recommendation: boolean;

    motion_poll_ballot_paper_selection: string;
    motion_poll_ballot_paper_number: number;
    motion_poll_default_type: string;
    motion_poll_default_100_percent_base: string;
    motion_poll_default_group_ids: Id[];

    users_sort_by: string;
    users_enable_presence_view: boolean;
    users_enable_vote_weight: boolean;
    users_enable_vote_delegations: boolean;
    users_allow_self_set_present: boolean;
    users_pdf_welcometitle: string;
    users_pdf_welcometext: string;
    users_pdf_url: string;
    users_pdf_wlan_ssid: string;
    users_pdf_wlan_password: string;
    users_pdf_wlan_encryption: string;
    users_email_sender: string;
    users_email_replyto: string;
    users_email_subject: string;
    users_email_body: string;

    assignments_export_title: string;
    assignments_export_preamble: string;

    assignment_poll_ballot_paper_selection: string;
    assignment_poll_ballot_paper_number: number;
    assignment_poll_add_candidates_to_list_of_speakers: boolean;
    assignment_poll_enable_max_votes_per_option: boolean;
    assignment_poll_sort_poll_result_by_votes: boolean;
    assignment_poll_default_type: string;
    assignment_poll_default_method: string;
    assignment_poll_default_100_percent_base: string;
    assignment_poll_default_group_ids: Id[];

    topic_poll_default_group_ids: Id[];

    poll_ballot_paper_selection: string;
    poll_ballot_paper_number: number;
    poll_sort_poll_result_by_votes: boolean;
    poll_default_type: string;
    poll_default_method: string;
    poll_default_100_percent_base: string;
    poll_default_group_ids: Id[];

// Group B
    present_user_ids: user/is_present_in_meeting_ids;

// Group C
    reference_projector_id: Id;
    default_projector_agenda_item_list_ids: Ids;
    default_projector_topic_ids: Ids;
    default_projector_list_of_speakers_ids: Ids;
    default_projector_current_list_of_speakers_ids: Ids;
    default_projector_motion_ids: Ids;
    default_projector_amendment_ids: Ids;
    default_projector_motion_block_ids: Ids;
    default_projector_assignment_ids: Ids;
    default_projector_mediafile_ids: Ids;
    default_projector_message_ids: Ids;
    default_projector_countdown_ids: Ids;
    default_projector_assignment_poll_ids: Ids;
    default_projector_motion_poll_ids: Ids;
    default_projector_poll_ids: Ids;

// Group D
    external_id: string;
    enable_anonymous: boolean;
    custom_translations: JSON;

// Group E
    organization_tag_ids: Id[];
    set_as_template: boolean;

// Group F
    jitsi_domain: string;
    jitsi_room_name: string;
    jitsi_room_password: string;
    enable_chat: boolean;
}
```

## Action
Updates the meeting.

If `set_as_template` is `True`, `template_for_organization_id` has to be set to `1`. If it is `False`, it has to be set to `None`.
`reference_projector_id` can only be set to a projector, which is not internal.

## Permissions
- Users with `meeting.can_manage_settings` can modify group A
- Users with `user.can_manage` can modify group B
- Users with `projector.can_manage` can modify group C
- Admins of the meeting can modify group D
- Users with CML `can_manage` or users with a OML of `can_manage_organization` can modify group E
- Only users with OML `superadmin` can modify group F
