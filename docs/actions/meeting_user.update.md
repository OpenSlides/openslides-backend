## Payload
```
{
// Required
    id: Id;

// Optional
// Group A
    number: string;
    structure_level_ids: Id[];
    vote_weight: decimal;
    comment: HTML;
    personal_note_ids: Id[];
    speaker_ids: Id[];
    supported_motion_ids: Id[];
    submitted_motion_ids: Id[];
    assignment_candidate_ids: Id[];
    projection_ids: Id[];
    chat_message_ids: Id[];
    vote_delegated_to_id: Id;
    vote_delegations_from_ids: Id[];

// Group B
    about_me: HTML;

// Group C
    group_ids: Id[];

// Group D
    assignment_candidate_ids: Id[];
    motion_working_group_speaker_ids: Id[];
    motion_editor_ids: Id[];
    supported_motion_ids: Id[];
    chat_message_ids: Id[];
}

```
## Internal action
Updates a meeting_user. `vote_delegated_to_id` and `vote_delegations_from_ids` has special checks, see user checks.

Will throw an error if the `group_ids` contain the meetings `anonymous_group_id`.