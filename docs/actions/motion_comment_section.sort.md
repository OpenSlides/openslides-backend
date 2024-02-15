## Payload
```
{
// Required
    meeting_id: Id;
    motion_comment_section_ids: Id[];
}
```

## Action
All `meeting/motion_comment_section_ids` of must be given in the new order. Sorts the sections with the `weight` field.

## Permissions
The request user needs `motion.can_manage`.
