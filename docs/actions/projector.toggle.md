## Payload
```js
{
    // required
    ids: Id[], // you can toggle on multiple projectors
    meeting_id: Id,
    content_object_id: Fqid,
    // optional
    options: JSON,
    stable: boolean,
    type: string,
}
```

## Action
Controls a slide on a single projector without modifying other projectors.
In contrast to `projector.project` this action does not affect all projectors of the meeting but only the given ones.

All projectors and content objects must belong to the same meeting given with `meeting_id` in the payload. For each projector:
- If there is a current equal projection: Removes the equal projection. If it was not stable, put it into the history.
- If there is no current equal projection: Creates a new current projection. If it is unstable, move all unstable projections to the history and set the projector scroll to 0.


## Permissions
The request user needs `projector.can_manage`
