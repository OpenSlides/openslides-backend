## Payload
```js
{id: Id;}
```

## Action
It is only allowed, if the given speaker is currently speaking. Sets the `end_time` of the current speaker to the current system time.

If `pause_time` is set, increase `total_pause` by `current_timestamp - pause_time` and set `pause_time` to `None`.

If `meeting/list_of_speakers_couple_countdown` is true, the countdown given by `meeting/list_of_speakers_countdown_id` must be *reset* (see [Countdowns](https://github.com/OpenSlides/OpenSlides/wiki/Countdowns#reset-a-countdown)).

If the given speaker has a `structure_level_id` set, the `current_start_time` of the structure level
has to be set to `None` and the spoken time of the speaker has to be substracted from the `remaining_time`. The spoken time is calculated as `(pause_time or end_time) - (unpause_time or begin_time)`.

## Permission
The request user needs `list_of_speakers.can_manage`.
