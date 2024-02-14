## Payload
```
{
    id: Id;
    mediafile_id: Id;
    place: string;
}
```

## Action
This action sets the `meeting/logo_<place>_id` relation to the `mediafile_id`. It must be checked, that it is a file and the mimetype is a valid logo (see [Mediafiles](https://github.com/OpenSlides/OpenSlides/wiki/Mediafiles)).

The logo can be unset via [meeting.unset_logo](meeting.unset_logo).

## Permissions
The user needs `meeting.can_manage_logos_and_fonts`
