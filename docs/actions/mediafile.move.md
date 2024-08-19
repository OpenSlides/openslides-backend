## Payload
```
{
    ids: Id[]
    parent_id: Id | null;
    owner_id: Fqid;
}
```

## Action
All mediafiles with `ids` should be added as children to `parent_id`. If `parent_id` is `null`, they are added to the root layer. `parent_id` must be a directory, if given. All given children and the parent, if given, must belong to the given `owner_id`.

The new children may not be published, if they are, there'll be an error.

If a file or directory is moved from a published directory to a non-published one,  `published_to_meetings_in_organization_id` is set to None and all related meeting_mediafiles are deleted for this file and all of its children. If a mediafile is moved from a non-published to a published directory, the file and all its children must have `published_to_meetings_in_organization_id` set to the organization id.

It must be ensured that no cycles are formed. The fields `inherited_access_group_ids` and `is_public` must be recalculated for all moved mediafiles that have meeting data (and their children) (including if they've just been moved to a published directory).

## Permissions
The request user needs `mediafile.can_manage` for meeting-wide mediafiles or the OML `can_manage_organization` for organization-wide mediafiles.
