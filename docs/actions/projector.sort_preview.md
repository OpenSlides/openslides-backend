## Payload
```js
{
    // required
    id: Id, // projector id
    projection_ids: Id[],
}
```

## Action
All projections from the projectors `projector/preview_projection_ids` must be given. The `projection/weight` is changed accordingly.

## Permissions
The request user needs `projector.can_manage`
