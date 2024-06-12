## Payload
```
{
// Required
    content_object_id: Fqid;
    meeting_id: Id;
    ids: Id[]

// Optional
    options: Object
    stable: boolean
    type: string
    keep_active_projections: boolean
}
```

## Action
Creates a new projection projection.

## Parameters
*ids*: The projectors where the projection will be displayed.

*type*: Defines the type of the projection.

*stable*: If set to a non true value all current non stable projections of the selected 
projectors are moved to history.

*keep_active_projections*: If set to true projections with the same type will not be removed
from projectors not specified in `ids`.

*options*: Can contain arbitrary data that will be added to the projection data.

## Permissions
The user needs `projector.can_manage`.
