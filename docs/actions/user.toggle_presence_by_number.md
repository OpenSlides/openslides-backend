## Payload

All fields are required
```js
{
  meeting_id: Id;
  number: String;
}
```

## Return
```js
{
  id: Id;
}
```

## Action

This action switches the presence of a user identified by their number. In the first place use the
field `meeting_user.number` to get the number for the given `meeting_id`

If the user's presence is `True` it will be changed to `False` by this action and vice versa. As a result, `meeting_id` is added/removed from `user/is_present_in_meeting_ids`.

If a user can not be identified by the given number (because there is no user with this number in the given meeting and their default number is empty, too, or there are at least two users with the same number in the given meeting), return with an error and a suitable error-message.

If the action is successful, it returns the id of the modified user. Thus the action-sender knows what user was modified.

## Permission

One of the following has to be true:
* The request user has the OML `can_manage_users`
* The request user has the CML `can_manage` in the given meeting's committee
* The request user has `user.can_manage` in the given meeting