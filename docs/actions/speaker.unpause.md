## Payload
```js
{id: Id;}
```

## Action
It is only allowed if the given speaker has `begin_time != None && end_time == None && pause_time != None`.

Unpauses the current speaker by increasing `total_pause` by `current_timestamp - pause_time` as well as setting `pause_time` to `None` and `unpause_time` to the current timestamp.

If `speaker/structure_level_list_of_speakers_id` is set, update the `structure_level_list_of_speakers` analogously to [speaker.speak](speaker.speak.md).

If `meeting/list_of_speakers_couple_countdown` is true, the countdown given by
`meeting/list_of_speakers_countdown_id` must be *started* (see
[Countdowns](https://github.com/OpenSlides/OpenSlides/wiki/Countdowns#start-a-countdown)).

## Permission
The request user needs `list_of_speakers.can_manage`.
