## Payload
Payload:
```
{
    id: Id;
    place: string;
}
```

## Action
Unsets the `meeting/logo_<place>_id` relation. The logo can be set via [[meeting.set_logo]].

## Permissions
The user needs `meeting.can_manage_logos_and_fonts`
