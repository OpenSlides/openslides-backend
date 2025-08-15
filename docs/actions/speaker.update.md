## Payload
```js
{
// Required
    id: Id;

// Optional
    speech_state: string;
    meeting_user_id: Id;
    structure_level_id: Id;
    point_of_order: bool;
    point_of_order_category_id: Id;
    note: string;

// Only if internal
    structure_level_list_of_speakers_id: Id;
    weight: int
}
```

## Action
Updates the given speaker. This table shows the conditions needed to change `speech_state`. _X_ is a
value for any of (None, contribution, pro, contra). The table state changes must be evaluated after
the permission check since it sets the global frame for these checks.

`meeting_user_id` is only allowed to be given if `speaker/meeting_user_id` is currently `None` and `speaker/speech_state` is `interposed_question`, `intervention` or `intervention_answer`.

If `speech_state` is changed from `intervention` or `intervention_answer` to any state that is not one of these two and the speaker has no `meeting_user_id`, it either needs to be set at the same time or there'll be an error.

`structure_level_id` is only allowed if the speaker is still waiting, i.e., `begin_time` is `None`. It is translated to a `structure_level_list_of_speakers_id` analogously to [speaker.create](speaker.create.md).


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

The point-of-order-related fields (`point_of_order`, `point_of_order_category_id` and `note`) follow
the same rules as in [speaker.create](speaker.create.md).

## Permissions
The request user needs either:
- `list_of_speakers.can_manage`
- `list_of_speakers.can_see` or `list_of_speakers.can_be_speaker` and the request user is the the speaker' user
