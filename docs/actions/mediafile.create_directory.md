## Payload
```js
{
// Required
    title: string;
    owner_id: Fqid;

// Optional
    parent_id: Id;
    access_group_ids: (group/mediafile_access_group_ids)[];
}
```

## Action

The given `owner_id` determines whether a meeting-wide or an organization-wide mediafile is uploaded. See [Mediafiles](https://github.com/OpenSlides/OpenSlides/wiki/Mediafiles) for more details.

The `parent_id`, if given, must be a directory (flag `mediafile/is_directory`) and belong to the same `owner_id`. The combination of `title` and `parent_id` must be unique (a file with one title can only exist once in a directory). `access_group_ids` can only be given for meeting-wide mediafiles and must then belong to the meeting given in `owner_id`.

Additional fields to set:
- `is_directory` must be set to `true`.
- `create_timestamp` must be set to the current timestamp.
- `mimetype`, `pdf_information`, `filesize`, `filename` and `token` must be left empty.
- `inherited_access_group_ids` and `is_public` must be calculated in case of a meeting-wide mediafile or a published orga-level parent (for those meetings where the parent has meeting_mediafiles).

## Permissions
The request user needs `mediafile.can_manage` for meeting-wide mediafiles or the OML `can_manage_organization` for organization-wide mediafiles.
