## Payload
```
{id: Id;}
```

## Action
Sets the state to *published*. Only allowed for polls in the *finished* state.

## Permissions
The request user needs:
- `motion.can_manage_polls` if the poll's content object is a motion
- `assignment.can_manage` if the poll's content object is an assignment
- `poll.can_manage` else
