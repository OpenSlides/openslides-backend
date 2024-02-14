## Payload
```
{
// Required
    id: Id;

// Optional
    name: string;
    prefix: string;
    motion_ids: Ids[];
}
```

## Action
Updates the category.

## Permissions
The request user needs `motion.can_manage`.
