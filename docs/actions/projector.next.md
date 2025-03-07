## Payload
```
{
    // required
    id: Id, // projector id
}
```

## Action
Add the lowest-weight projection in `projector/preview_projection_ids` to `projector/current_projection_ids` and remove it from the preview.
Moves all unstable projections in `projector/current_projection_ids` to the history.
Does nothing, if there is no projection in the `projector/preview_projection_ids`. 

## Permissions
The request user needs `projector.can_manage`
