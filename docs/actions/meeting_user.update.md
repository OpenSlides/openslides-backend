## Payload
```js
{
// Required
    id: Id;

// Optional
// Group A
    number: string;
    structure_level_ids: Id[];
    vote_weight: decimal;
    comment: HTML;
    locked_out: boolean;

// Group B
    about_me: HTML;

// Group C
    group_ids: Id[];

// Group D
    assignment_candidate_ids: Id[];
    motion_working_group_speaker_ids: Id[];
    motion_editor_ids: Id[];
    motion_supporter_ids: Id[];
    chat_message_ids: Id[];
}

```
## Internal action
Will throw an error if the `group_ids` contain the meetings `anonymous_group_id`.

The action checks, whether at the end the field `locked_out` will be set together with any of `user.can_manage` or any admin statuses on the updated meeting_user and throws an error if that is the case.
