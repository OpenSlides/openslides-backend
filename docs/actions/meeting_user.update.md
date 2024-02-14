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
}
// Group C
    group_ids: Id[];
}

```
## Action
Updates a meeting_user. `vote_delegated_to_id` and `vote_delegations_from_ids` has special checks, see user checks.

## Permissions
Group A: The request user needs `user.can_manage`.

Group B: The request user needs `user.can_manage` or must be the request user

Group C: The request user must satisfy at least one of:
- the OML `can_manage_users`
- `user.can_manage` for the meeting
- The CML `can_manage` for the committee of the meeting