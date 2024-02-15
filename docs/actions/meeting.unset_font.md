## Payload
Payload:
```
{
    id: Id;
    place: string;
}
```

## Action
Unsets the `meeting/font_<place>_id` relation. The font can be set via [meeting.set_font](meeting.set_font.md).

## Permissions
The user needs `meeting.can_manage_logos_and_fonts`
