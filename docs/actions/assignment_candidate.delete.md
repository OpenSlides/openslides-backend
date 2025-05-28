## Payload
```js
{ id: Id; }
```

## Action
Deletes an assignment candidate for the assignment. It is forbidden to remove a candidate from a finished assignment if the action is called externally.

## Permissions
If the `assignment_candidate/user_id` is equal to the request user id, the user needs `assignment.can_nominate_self`, else the user needs `assignment.can_nominate_other`.

In both cases: If the assignment phase is `voting`, the request user also needs `assignment.can_manage`.
