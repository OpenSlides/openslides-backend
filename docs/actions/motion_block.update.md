## Payload
```
{
// Required
    id: number;

// Optional
    title: string;
    internal: boolean;
    motion_ids: Id[];
}
```

## Action
Updates the motion block.

## Permissions
The request user needs `motion.can_manage`.
