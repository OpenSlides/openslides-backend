## Payload
```js
{
// Required
    mediafile_id: Id;
    meeting_id: Id;
    is_public: boolean;

// Optional
    access_group_ids: Id[]
    inherited_access_group_ids: Id[]
    used_as_font_bold_in_meeting_id: Id
    used_as_font_bold_italic_in_meeting_id: Id
    used_as_font_chyron_speaker_name_in_meeting_id: Id
    used_as_font_italic_in_meeting_id: Id
    used_as_font_monospace_in_meeting_id: Id
    used_as_font_projector_h1_in_meeting_id: Id
    used_as_font_projector_h2_in_meeting_id: Id
    used_as_font_regular_in_meeting_id: Id
    used_as_logo_pdf_ballot_paper_in_meeting_id: Id
    used_as_logo_pdf_footer_l_in_meeting_id: Id
    used_as_logo_pdf_footer_r_in_meeting_id: Id
    used_as_logo_pdf_header_l_in_meeting_id: Id
    used_as_logo_pdf_header_r_in_meeting_id: Id
    used_as_logo_projector_header_in_meeting_id: Id
    used_as_logo_projector_main_in_meeting_id: Id
    used_as_logo_web_header_in_meeting_id: Id
}
```

## Internal action
The action creates a meeting_mediafile item.
Calculations pertaining to the validity of the data are mostly expected to be carried out in the calling action.
The only exceptions are, that the action will raise exceptions if:
- The mediafile is an unpublished organization file, or
- The mediafile already has a meeting_mediafile in this meeting.
