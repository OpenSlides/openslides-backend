### Includes changes of feature branch `los-extension`!

## Payload
```
{
// Required
    id: Id;

// Optional
    speech_state: string;
    meeting_user_id: Id;
    structure_level_id: Id;
}
```

## Action
Updates the given speaker. This table shows the conditions needed to change `speech_state`. _X_ is a
value for any of (None, contribution, pro, contra). The table state changes must be evaluated after
the permission check since it sets the global frame for these checks.

`meeting_user_id` is only allowed to be given if `speaker/meeting_user_id` is currently `None` and `speaker/speech_state` is `interposed_question`.

`structure_level_id` is only allowed if the speaker is still waiting, i.e., `begin_time` is `None`. It is translated to a `structure_level_list_of_speakers_id` analogously to [[speaker.create]].


| From         | To           | Conditions  |
| ------------ | ------------ | --------------------- |
| X            | X            | no change, no conditions -> allowed   |
| X            | contribution | `list_of_speakers.can_manage` or `meeting/list_of_speakers_can_set_contribution_self` is true |
| X            | pro/contra   | `meeting/list_of_speakers_enable_pro_contra_speech` is true |
| contribution | None         | `list_of_speakers.can_manage` or `meeting/list_of_speakers_can_set_contribution_self` is true |
| pro/contra   | None         | `meeting/list_of_speakers_enable_pro_contra_speech` is true |
| X            | intervention | `meeting/list_of_speakers_intervention_time > 0` |
| X            | interposed_question | forbidden |
| interposed_question | X | forbidden |

## Permissions
The request user needs either:
- `list_of_speakers.can_manage`
- `list_of_speakers.can_see` or `list_of_speakers.can_be_speaker` and the request user is the the speaker' user
