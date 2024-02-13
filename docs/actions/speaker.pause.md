### Includes changes of feature branch `los-extension`!

## Payload
```
{id: Id;}
```

## Action
It is only allowed if the given speaker has `begin_time != None && end_time == None && pause_time == None`.

Pauses the current speaker by setting `pause_time` to the current timestamp.

If `speaker/structure_level_list_of_speakers_id` is set, update the `structure_level_list_of_speakers` analogously to [[speaker.end_speech]].

If `meeting/list_of_speakers_couple_countdown` is true, the countdown given by
`meeting/list_of_speakers_countdown_id` must be *stopped* (see
[[Countdowns#restart-a-countdown]]).

## Permission
The request user needs `list_of_speakers.can_manage`.
