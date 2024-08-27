## Payload
```js
{
// Required
    id: Id;
    publish: boolean;
}
```

## Action
Publishes or unpublishes the mediafile depending on the value of `is_published_to_meetings`.
Can only be used on root-level organization-owned mediafiles.

`is_published_to_meetings` is set to the value of `publish` on the given mediafile.
If `publish` is true, the given mediafile and all its children will have `published_to_meetings_in_organization_id` set to the orga id. If not, `published_to_meetings_in_organization_id` will be set to None on all of these models and their meeting_mediafiles will all be deleted.

## Permissions
The request user needs the OML `can_manage_organization`.
