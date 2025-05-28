## Payload
```js
{
    // required
    id: Id, // projection id
}
```

## Action
Adds the given projection to `projector/current_projection_ids` and remove it from the preview.
Moves all unstable projections in `projector/current_projection_ids` to the history.
The given projection must be in a preview of a projector.

## Permissions
The request user needs `projector.can_manage`
