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

It must be ensured that no cycles are formed. The fields `inherited_access_group_ids` and `is_public` must be recalculated in case of a meeting-wide mediafile.

## Permissions
The request user needs `mediafile.can_manage` for meeting-wide mediafiles or the OML `can_manage_organization` for organization-wide mediafiles.
