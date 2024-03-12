## Payload
```
{
// Required
    list_of_speakers_id: Id;
    meeting_user_id: Id;  // except if speech_state == interposed_question, see below

// Optional
    speech_state: string;
    point_of_order: boolean;
    note: string;
    point_of_order_category_id: Id;
    structure_level_id: Id;
}
```

## Action
Two types of operation:
- *adding oneself* (`meeting_user_id` belongs to the request user):

  If it is:
  - (not a point of order or `meeting/list_of_speakers_closing_disables_point_of_order` is set) and
  - the list of speakers is closed and
  - the request user has not `list_of_speakers.can_manage`

  the request must be rejected due to a closed list. All other cases are allowed.

- *adding another user* (`meeting_user_id` does *not* belong to the request user) is allowed with
  conditions see under **Permissions**. If `point_of_order` is also `true`, it is only allowed if
  `meeting.list_of_speakers_can_create_point_of_order_for_others` is `true` as well.

`meeting_user_id` is _not_ required if `speech_state == "interposed_question"`.

There are many things to watch out for:
- Point of order speakers are only allowed if `meeting/list_of_speakers_enable_point_of_order_speakers` is true.
- `note` is only allowed if it `point_of_order` is true.
- `point_of_order_category_id` is only allowed and in this case required, if `point_of_order` is true and `meeting.list_of_speakers_enable_point_of_order_categories` is also true. This opens an alternative way to get the point-of-order-speakers sorted, see [Point of order](https://github.com/OpenSlides/OpenSlides/wiki/List-of-speakers#point-of-order).
- If `meeting/list_of_speakers_present_users_only` is true, the user must be present (`user/present_in_meeting_ids`).
- The `weight` must be calculated as described in [Point of order](https://github.com/OpenSlides/OpenSlides/wiki/List-of-speakers#point-of-order) with an eye to detail regarding point of order speakers.
- If `meeting.list_of_speakers_allow_multiple_speakers` is `False`, the given user must not be already waiting. It is allowed to have the user once as a normal speaker and once as a point of order speaker, but not two speakers of the same type.
- The user must belong to the meeting.
- `speech_state` can only be set to `pro` or `contra` if `meeting/list_of_speakers_enable_pro_contra_speech` is true
- `speech_state` can only be set to `contribution` if `list_of_speakers.can_manage` or
  `meeting/list_of_speakers_can_set_contribution_self` is true
- `speech_state` can only be set to `intervention` if `meeting/list_of_speakers_intervention_time > 0`
- `speech_state` can only be set to `interposed_question` if
  `meeting/list_of_speakers_enable_interposed_question` is true
- If `speech_state == "interposed_question"`, the speaker has to be sorted after all other
  interposed questions, but before all other speakers (including point of order speakers)
- The speech states `intervention` and `interposed_question` cannot be combined with `point_of_order == True`

If the optional `structure_level_id` is given, it is checked whether a
`structure_level_list_of_speakers` for this LOS and structure level exists. If it doesn't, it is
first created. Then, its `id` is added to the speaker instance.

`structure_level_id` is only allowed if `meeting/list_of_speakers_default_structure_level_time > 0`.

## Permissions
- adding oneself: The request user needs `list_of_speakers.can_be_speaker`. Also see conditions above.
- adding another user: The request user needs `list_of_speakers.can_manage`.
