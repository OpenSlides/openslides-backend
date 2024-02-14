## Payload
```
{
// Required
    id: Id;

// Optional
    text: HTML;
    rejected: boolean;
    internal: boolean;
    type: number;
    other_description: string;
}
```

## Action
Updates the given change recommendation.

## Permissions
The request user needs `motion.can_manage`.
