## Payload
```
{
\\ Required
    id: Id;

\\ Optional
    title: string;
    access_group_ids: (group/mediafile_access_group_ids)[];  // only for meeting-wide mediafiles
    token: string,                                           // only for organization-wide mediafiles
}
```

## Action
Updates the mediafile. The combination of `title` and `parent_id` must be unique (a file with one title can only exist once in a directory). `access_group_ids` can only be given for meeting-wide mediafiles and must then belong to the meeting given in `owner_id`. `token` can only be given for organization-wide mediafiles and must be unique across all of them. `inherited_access_group_ids` and `is_public` must recalculated if `access_group_ids` is given. See [Mediafiles](https://github.com/OpenSlides/OpenSlides/wiki/Mediafiles).

## Permissions
The request user needs `mediafile.can_manage` for meeting-wide mediafiles or the OML `can_manage_organization` for organization-wide mediafiles.
