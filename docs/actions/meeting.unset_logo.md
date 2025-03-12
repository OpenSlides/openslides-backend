## Payload
Payload:
```js
{
    id: Id;
    place: string;
}
```

## Action
Unsets the `meeting/logo_<place>_id` relation. The logo can be set via [meeting.set_logo](meeting.set_logo.md).

## Permissions
The user needs `meeting.can_manage_logos_and_fonts`
