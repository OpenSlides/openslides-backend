## Payload
```js
{
// Required
    id: Id;
}
```

## Action
Archives the meeting by setting the is_active_in_organization_id to `None`.

This fails if meeting has ongoing polls or an active speaker.

## Permissions
archive a meeting is allowed with CML can_manage or OML can_manage_organization rights
