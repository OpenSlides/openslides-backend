## Payload
```
{
    motion_id: Id;
    motion_editor_ids: Id[];
}
```

## Action
All `motion_editor_ids` of all editors of the motion must be given in the new order. The `weight` field is set accordingly.

## Permissions
The request user needs `can_manage_metadata`.
