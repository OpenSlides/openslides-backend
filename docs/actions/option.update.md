## Payload
```
{
// Required
    id: Id;
// Optional.
    Y: number;
    N: number;
    A: number;
    publish_immediately: boolean;
}
```

## Action
It is only allowed for analog polls. Updating this option changes the associated `vote` objects for `Y`, `N` and `A` to the given values.

If the poll's state is *created* and at least one vote value is given (`Y`, `N` or `A`), the state must be set to *finished*. if additionally `publish_immediately` is given, the state must be set to *published*.

## Permissions
The request user needs:
- `motion.can_manage_polls` if the poll's content object is a motion
- `assignment.can_manage` if the poll's content object is an assignment
- `poll.can_manage` if the poll's content object is a topic
