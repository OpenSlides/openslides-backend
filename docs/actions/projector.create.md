## Payload
```
{
    // Required
    name: string,
    meeting_id: Id,

    // Optional
    is_internal: boolean,
    width: number,
    aspect_ratio_numerator: number,
    aspect_ratio_denominator: number,
    color: string,
    background_color: string,
    header_background_color: string,
    header_font_color: string,
    header_h1_color: string,
    chyron_background_color: string,
    chyron_font_color: string,
    show_header_footer: boolean,
    show_title: boolean,
    show_logo: boolean,
    show_clock: boolean,

    used_as_reference_projector_meeting_id: Id,
    used_as_default_projector_for_agenda_item_list_in_meeting_id: Id,
    used_as_default_projector_for_topic_in_meeting_id: Id,
    used_as_default_projector_for_list_of_speakers_in_meeting_id: Id,
    used_as_default_projector_for_current_los_in_meeting_id: Id,
    used_as_default_projector_for_motion_in_meeting_id: Id,
    used_as_default_projector_for_amendment_in_meeting_id: Id,
    used_as_default_projector_for_motion_block_in_meeting_id: Id,
    used_as_default_projector_for_assignment_in_meeting_id: Id,
    used_as_default_projector_for_mediafile_in_meeting_id: Id,
    used_as_default_projector_for_message_in_meeting_id: Id,
    used_as_default_projector_for_countdown_in_meeting_id: Id,
    used_as_default_projector_for_assignment_poll_in_meeting_id: Id,
    used_as_default_projector_for_motion_poll_in_meeting_id: Id,
    used_as_default_projector_for_poll_in_meeting_id: Id,
}
```

## Action
Creates a new projector.
- All color strings must match `^#[0-9a-f]{6}$`
- `is_internal` may not be set if the `projector/used_as_reference_projector_meeting_id` relation is set.

## Permissions
The request user needs `projector.can_manage`
