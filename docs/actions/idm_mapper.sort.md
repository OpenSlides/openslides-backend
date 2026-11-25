## Payload
```js
{
    // Required
    idm_mapper_ids: Id[];
}
```

## Action
Sorts all idm_mappers of the organization into the order within `idm_mapper_ids`.

Will not work if `idm_mapper_ids` does not contain exactly all of the mapper ids that exist.

## Permissions
The user needs OML `can_manage_organization`.