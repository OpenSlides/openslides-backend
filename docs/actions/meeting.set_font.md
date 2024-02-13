## Payload
```
{
    id: Id;
    mediafile_id: Id;
    place: string;
}
```

## Action
This action sets the `meeting/font_<place>_id` relation to the `mediafile_id`. It must be checked, that it is a file and the mimetype is a valid font (see [[Mediafiles]]).

The font can be unset via [[meeting.unset_font]].

## Permissions
The user needs `meeting.can_manage_logos_and_fonts`
