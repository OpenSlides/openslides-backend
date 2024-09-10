## Payload
```
{
\\ Required
    id: Id;

\\ Optional
    title: string;
    token: string,                                           // only for organization-wide mediafiles
    meeting_id: Id; // If meeting-related data is to be changed, this needs to contain the meeting id
    access_group_ids: (group/meeting_mediafile_access_group_ids)[];  // only for meeting-wide mediafiles
}
```

## Action
Updates the mediafile. The combination of `title` and `parent_id` must be unique (a file with one title can only exist once in a directory). `access_group_ids` can be given for meeting-wide mediafiles or published organization mediafiles and must then belong to the meeting named through `meeting_id`, also if the mediafile is meeting-related, the `meeting_id` field must point to the same meeting as the mediafiles `owner_id`. `token` can only be given for organization-wide mediafiles and must be unique across all of them. `inherited_access_group_ids` and `is_public` must recalculated if `access_group_ids` is given. See [Mediafiles](https://github.com/OpenSlides/OpenSlides/wiki/Mediafiles).

## Permissions
The request user needs `mediafile.can_manage` for meeting-wide mediafiles or the OML `can_manage_organization` for organization-wide mediafiles.
