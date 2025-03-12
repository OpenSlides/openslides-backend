## Payload
```js
{
    // required
    id: Id, // projector id
}
```

## Action
Adds the highest-weight projection in `projector/history_projection_ids` to `projector/current_projection_ids` and remove it from the history.
Moves all unstable projections in `projector/current_projection_ids` to the front of the preview, so they get `min(weight)-1` weight.
Does nothing, if there is no projection in the `projector/history_projection_ids`.

## Permissions
The request user needs `projector.can_manage`
