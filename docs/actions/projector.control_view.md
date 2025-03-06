## Payload
```
{
    // required
    id: Id,
    field: "scale" | "scroll",
    direction: "up" | "down" | "reset",
    // optional
    step: number,
}
```

## Action

Calling this action modifies the given field. Directions:

- up: Add `step` (1 as default) to the field
- down: Subtract `step` (1 as default) from the field
- reset: Set the field to 0

If the given `step` is less than 1 it is set to 1.

## Permissions
The request user needs `projector.can_manage`
