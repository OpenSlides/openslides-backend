## Payload
```
{
    meeting_id: Id;
    statute_paragraph_ids: Id[];
}
```

## Action
All `statute_paragraph_ids` of the meeting must be given in the new order. Sets the `weight` field accordingly.

## Permissions
The request user needs `motion.can_manage`.
