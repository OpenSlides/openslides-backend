## Payload
```
{
// Required
    line_from: number;
    line_to: number;
    text: HTML;
    motion_id: Id;

// Optional
    rejected: boolean;
    internal: boolean;
    type: string;
    other_description: string;
}
```

## Action
Creates a new motion change recommendation. The `creation_time` must be set to the current time. It must be `line_to >= line_from`. It must be checked that there are no other change recommendation for the given motion that *collide* with the change recommendation to create.

Two change recommendations `a` and `b` are *disjunct* if the intervals given by `line_from` and `line_to` are not overlapping, meaning one of these conditions must be true:
- `a.line_from < b.line_from` and `a.line_to < b.line_from`
- `a.line_from > b.line_to` and `a.line_to > b.line_to`

As `a.line_from <= a.line_to` already holds, it can be simplified to:
- `a.line_to < b.line_from`
- `a.line_from > b.line_to`

Two change recommendations are *colliding* if they are not disjunct.

`line_from` and `line_to` must both be greater than 0. The only exception is if they are both 0, which describes a title change recommendation.

## Permissions

The request user needs `motion.can_manage`.
