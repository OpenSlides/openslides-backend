## Payload
```js
{
// optional
    allow_abstain: boolean;
    allow_nota: boolean;
    display_chart: string;
    group_ids: Id[]
    onehundred_percent_base: string;
    sort_result_by_votes: boolean;
    strike_out: boolean;
    visibility: string;
}
```

## Internal action

The action updates a `meeting_poll_default` item.

Should only be called by meeting.update.

All ids in `group_ids` must bellong to the meeting defined by `meeting_id`.
