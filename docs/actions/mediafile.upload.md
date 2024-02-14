## Payload
```js
{
// Required
    owner_id: Fqid;
    file: string; // base64 encoded
    filename: string;
    title: string;

// Optional
    parent_id: Id;
    access_group_ids: (group/mediafile_access_group_ids)[];  // only for meeting-wide mediafiles
    token: string,                                           // only for organization-wide mediafiles
}
```

## Action

The given `owner_id` determines whether a meeting-wide or an organization-wide mediafile is uploaded. See [Mediafiles](https://github.com/OpenSlides/OpenSlides/wiki/Mediafiles) for more details.

The `parent_id`, if given, must be a directory (flag `mediafile/is_directory`) and belong to the same `owner_id`. The combination of `title` and `parent_id` must be unique (a file with one title can only exist once in a directory). `access_group_ids` can only be given for meeting-wide mediafiles and must then belong to the meeting given in `owner_id`. `token` can only be given for organization-wide mediafiles and must be unique across all of them.

Additional fields to set:
- `is_directory` must be set to `false`.
- `create_timestamp` must be set to the current timestamp.
- `inherited_access_group_ids` and `is_public` must be calculated in case of a meeting-wide mediafile.
- `mimetype` is guessed by the ~~`filename`~~ `filecontent` (since 4.0.16)
- `pdf_information`: If the mimetype is `aplication/pdf` this object needs to be filled:
    ```
    {
        pages: number;
        encrypted: boolean;
    }
    ```
    It is tried to get the amount of pages from the pdf. If it is encrypted or the extraction fails `pages` will be set to 0 and `entrypted` to true.
- `filesize`: Size of the file in bytes.

The `file` is not stored into the datastore but uploaded to the mediaservice.

## Permissions
The request user needs `mediafile.can_manage` for meeting-wide mediafiles or the OML `can_manage_organization` for organization-wide mediafiles.
