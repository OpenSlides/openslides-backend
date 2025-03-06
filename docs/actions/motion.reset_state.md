## Payload
```
{ id: Id; }
```

## Action
Resets the state to the workflow's first state. Note that the same logic for `motion/number` is executed as in [motion.set_state](motion.set_state.md).

If `set_workflow_timestamp` is set in the new state of the motion, `workflow_timestamp` is set to the current timestamp, otherwise it is reset.

## Permissions
The request user needs `motion.can_manage_metadata`.
