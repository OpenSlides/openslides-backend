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

## Permissions
The user needs `user.can_manage` to change `name` and `permission`, for `external_id` meeting admin rights are mandatory.
