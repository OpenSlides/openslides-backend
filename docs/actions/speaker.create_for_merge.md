## Payload
```
{
// Required
    list_of_speakers_id: Id;
    meeting_user_id: Id;
    weight: int,

// Optional
    begin_time: int;
    end_time: int;
    unpause_time: int;
    total_pause: int;
    speech_state: string;
    point_of_order: boolean;
    note: string;
    point_of_order_category_id: Id;
    structure_level_list_of_speakers_id: Id;
}
```

## Internal action
Creates speakers with specific data.
Unlike [speaker.create](speaker.create.md) this is a multi action with pretty much no checks. `meeting_id` is generated from the `list_of_speakers_id`
Should only be called by [user.merge_together](user.merge_together.md).