## Payload
```
{
// required
    assignment_id: Id;
    meeting_user_id: Id;
}
```

## Action
Creates an assignment candidate for the assignment. It is forbidden, if the assignment phase is `finished`.

## Permissions
If the `meeting_user_id` is equal the meeting_user with the request user id, the user needs `assignment.can_nominate_self`, else the user needs `assignment.can_nominate_other`.

In both cases: If the assignment phase is `voting`, the request user also needs `assignment.can_manage`.
