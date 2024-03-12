## Payload
```
{
    motion_id: Id;
    motion_submitter_ids: Id[];
}
```

## Action
All `motion_submitter_ids` of all submitters of the motion must be given in the new order. The `weight` field is set accordingly.

## Permissions
The request user needs `can_manage_metadata`.
