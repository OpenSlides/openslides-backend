## Payload
```js
{
// Required
    id: Id;

// Optional
    text: HTML;
    rejected: boolean;
    internal: boolean;
    type: number;
    other_description: string;
    line_from: number;
    line_to: number;
}
```

## Action
Updates the given change recommendation.

## Permissions
The request user needs `motion.can_manage`.
