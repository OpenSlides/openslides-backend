## Payload
```
{ id: Id; }
```

## Action
Deletes the given projection.
Fails if
- the projection has no `current_projector_id` and
- the projection has no `preview_projector_id`

## Permissions
The request user needs `projector.can_manage`
