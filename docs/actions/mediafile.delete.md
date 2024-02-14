## Payload
```
{
    id: Id;
}
```

## Action
This recursively deletes all child-mediafiles (if the given one is a directory). The mediafiles must not be deleted from the mediaservice.

## Permissions
The request user needs `mediafile.can_manage` for meeting-wide mediafiles or the OML `can_manage_organization` for organization-wide mediafiles.
