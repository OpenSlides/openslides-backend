## Payload
```
{
// Optional
// either:
    id: Id;
// or:
    user_id: Id;
    meeting_id: Id

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
}

```
## Internal action
Sets the data for a meeting user identified either by an `id` or a `user_id`-`meeting_id` pair. If the latter is the case and there is no meeting user with that combination, a new one is created.