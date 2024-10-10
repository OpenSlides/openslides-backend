## Payload
```
{
// Required
    id: Id,

// Optional
    name: string,
    permissions: string[],
    external_id: string,
}
```

## Action
Updates the group. Permissions are restricted to the following enum: https://github.com/OpenSlides/openslides-backend/blob/fae36a0b055bbaa463da4768343080c285fe8178/global/meta/models.yml#L1621-L1656

If the group is the meetings anonymous group, the name may not be changed and the permissions have to be in the following whitelist:
- agenda_item.can_see,
- agenda_item.can_see_internal,
- assignment.can_see,
- list_of_speakers.can_see,
- list_of_speakers.can_see_moderator_notes,
- mediafile.can_see,
- meeting.can_see_autopilot,
- meeting.can_see_frontpage,
- meeting.can_see_history,
- meeting.can_see_livestream,
- motion.can_see,
- motion.can_see_internal,
- projector.can_see,
- user.can_see,
- user.can_see_sensitive_data

## Permissions
The user needs `user.can_manage` to change `name` and `permission`, for `external_id` meeting admin rights are mandatory.
