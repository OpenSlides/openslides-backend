## Payload
```
{
// Required
    id: Id;

// Optional
    name: string;
    first_state_id: Id;
}
```

## Action
Updates the motion workflow. The `first_state_id` must be a state of this workflow.

## Permissions
The request user needs `motion.can_manage`.
