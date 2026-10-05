## Payload
```js
{
// optional
    allow_live_voting: boolean;
    default_live_voting_enabled: boolean;
    default_method: string;
    default_required_majority: string;
    enable_cumulative_voting: boolean;
    enable_max_options_limit: boolean;
    enable_max_yes_votes: boolean;
    group_ids: Id[];
    onehundred_percent_base: string;
    sort_result_by_votes: boolean;
    visibility: string;
}
```

## Internal action

The action updates a `meeting_poll_default` item.

Should only be called by meeting.update.

All ids in `group_ids` must bellong to the meeting defined by `meeting_id`.
