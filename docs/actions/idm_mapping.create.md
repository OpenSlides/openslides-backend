## Payload
```js
{
    // Required
    idm_field: string;
    os_field: string;
    mapper_id: Id;
    // Optional
    default_value: string;
    allow_update: boolean;
    override_default: boolean;
}
```

## Action
Creates a new idm_mapping.

## Permissions
The user needs OML `can_manage_organization`.