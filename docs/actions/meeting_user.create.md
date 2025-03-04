## Payload
```
{
// Required
    user_id: Id;
    meeting_id: Id;

// Optional
// Group A
    number: string;
    structure_level: string;
    vote_weight: decimal;
    comment: HTML;
    personal_note_ids: Id[];
    speaker_ids: Id[];
    supported_motion_ids: Id[];
    submitted_motion_ids: Id[];
    assignment_candidate_ids: Id[];
    projection_ids: Id[];
    chat_message_ids: Id[];
    locked_out: boolean;

// Group B
    about_me: HTML;

// Group C
    group_ids: Id[];
}
```

## Action
The action creates a meeting_user item.
If `locked_out` is set, it checks against the present `user.can_manage` and all admin statuses and throws an error if any are present.

Will throw an error if the `group_ids` contain the meetings `anonymous_group_id`.

## Permissions
Group A: The request user needs `user.can_manage`.

Group B: The request user needs `user.can_manage` or must be the request user.

Group C: The request user must satisfy at least one of:
- the OML `can_manage_users`
- `user.can_manage` for the meeting
- the CML `can_manage` for the committee of the meeting
