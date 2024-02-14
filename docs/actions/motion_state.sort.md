(NOT IMPLEMENTED)

## Payload

```js
{
    workflow_id: Id;
    motion_state_ids: Id[];
}
```

## Action

This action sets the `weight`-field of each motion_state in a specified workflow according to the sent `tree`. The first item gets the lowest weight, whereover the last item gets the highest weight.
The sent `motion_state_ids` must include every motion_state in the specified workflow.

## Permission

A user needs at least `motion.can_manage`.