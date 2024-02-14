## Payload
```
{id: Id;}
```

## Action
It is only allowed, if the given speaker is waiting.

If the given speaker has `speech_state == "interposed_question"`, pause the current speaker via `speaker.pause`. Otherwise, stop the current speaker (if it exists) via `speaker.end_speech`.

Starts the speech of the given speaker: Sets `begin_time` to the current system time.

If `meeting/list_of_speakers_couple_countdown` is true, the countdown given by
`meeting/list_of_speakers_countdown_id` must be *restarted* (see
[Countdowns](https://github.com/OpenSlides/OpenSlides/wiki/Countdowns#restart-a-countdown)).
If the given speaker has `speech_state == "intervention"`, the `countdown_time` of the countdown has to be set to `current_timestamp + meeting/list_of_speakers_intervention_time` first.
If the given speaker has `speech_state == "interposed_question"`, the `countdown_time` of the countdown has to be set to `current_timestamp` first. 

If the given speaker has a `structure_level_id` set, the `current_start_time` of the structure level
has to be set to the speaker's `begin_time`.

## Permission
The request user needs `list_of_speakers.can_manage`.
