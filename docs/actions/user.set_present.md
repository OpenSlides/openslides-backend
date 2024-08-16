## Payload
```
{
    // Required
    id: Id;
    meeting_id: Id;
    present: boolean;
}
```

## Action
Sets the user's present status in the given meeting. If `present` is true, `meeting_id` is added to `is_present_in_meeting_ids`, otherwise it's removed.

## Permissions

One of the following has to be true:
* The meeting is not locked via the setting `locked_from_inside` and:
   * The request user has the OML `can_manage_users`
   * The request user has the CML `can_manage` in the given meeting's committee
* The request user has `user.can_update` or `user.can_manage_presence` in the given meeting
* The `user_id` is equal to the request user id and the setting `users_allow_self_set_present` is set to `True` in the given meeting
