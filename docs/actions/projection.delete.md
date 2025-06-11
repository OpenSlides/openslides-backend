## Payload
```js
{ id: Id; }
```

## Action
Deletes the given projection.
It is only allowed to do so for projections with the `current_projector_id` or `preview_projector_id` relation set.

## Permissions
The request user needs `projector.can_manage`
