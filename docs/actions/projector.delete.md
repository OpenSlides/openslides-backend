## Payload
```js
{
    id: Id,
}
```

## Action
Deletes the projector.
Fails if the projector is the meetings reference projector. If
the projector was the default projector for some collections
(`used_as_default_projector_for_*_in_meeting_id`), the reverse relations are changed to the
`meeting/reference_projector_id`.

## Permissions
The request user needs `projector.can_manage`
