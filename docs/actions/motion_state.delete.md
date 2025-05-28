## Payload
```js
{ id: Id; }
```

## Action
Deletes the state. It must fail, if the state is the first state of the workflow.

## Permissions
The request user needs `motion.can_manage`.
