## Payload
```js
{
// required
    meeting_id: Id;

// exactly 1 out of 3 is required
    used_as_assignment_poll_config_in_meeting_id: Id;
    used_as_motion_poll_config_in_meeting_id: Id;
    used_as_topic_poll_config_in_meeting_id: Id;

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

The action creates `meeting_poll_setting` item for the meeting. Should only be called by meeting.create or meeting.update.

Along with the `meeting_id` field, exactly one out of the 3 field must be defined:

* used_as_assignment_poll_config_in_meeting_id
* used_as_motion_poll_config_in_meeting_id
* used_as_topic_poll_config_in_meeting_id

Value in the field used_as_*_poll_config_in_meeting_id must be the same as `meeting_id`.

All ids in `group_ids` must bellong to the meeting defined by `meeting_id`.

This action sets default values based on the poll type for the fields listed below if no value is given for them in the payload:

* visibility:
  * if `used_as_topic_poll_config_in_meeting_id` is set => "manually"
  * else => "secret"
