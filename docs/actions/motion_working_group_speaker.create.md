## Payload
```js
{
// required
    meeting_user_id: Id;
    motion_id: Id;
}
```

## Action
Creates a new working group speaker. The user and motion must belong to the same meeting. The fields
If the conjunction of the fields `meeting_user_id` and `motion_id` is not unique, an exception is raised. This way it is asserted that the user doesn't already exist as a working group speaker.
The `weight` is set to the maximum of all working group speakers of the
motion plus 1.

## Permissions
The request user needs `can_manage_metadata`.
