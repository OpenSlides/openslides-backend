## Payload
```
{
    assignment_id: Id;
    candidate_ids: Id[];
}
```

## Action
Expects all `assignment/candidate_ids` to be included, but given in the new order.

## Permissions
The  user also needs `assignment.can_manage`.
