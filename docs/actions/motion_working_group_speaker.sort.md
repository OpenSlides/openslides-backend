## Payload
```js
{
    motion_id: Id;
    motion_working_group_speaker_ids: Id[];
}
```

## Action
All `motion_working_group_speaker_ids` of all working group speakers of the meeting must be given in the new order. The `weight` field is set accordingly.

## Permissions
The request user needs `can_manage_metadata`.
