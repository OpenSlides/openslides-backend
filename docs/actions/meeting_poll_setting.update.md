## Payload
```js
{
// optional
    allow_live_voting: boolean;
    group_ids: Id[];
    enable_cumulative_voting: boolean;
    enable_live_voting: boolean;
    enable_max_options_limit: boolean;
    enable_max_yes_votes: boolean;
    method: string;
    onehundred_percent_base: string;
    required_majority: string;
    sort_result_by_votes: boolean;
    visibility: string;
}
```

## Internal action

The action updates a `meeting_poll_setting` item.

Should only be called by meeting.update.

All ids in `group_ids` must bellong to the meeting defined by `meeting_id`.
