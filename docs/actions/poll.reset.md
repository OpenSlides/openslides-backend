## Payload
```
{id: Id;}
```

## Action
Sets the state to *created*. Only allowed for polls in the *finished* or *published* state. All vote objects of all options (including the global option) are deleted.

If `type != "pseudoanonymous"`, `is_pseudoanonymized` may be reset to `false` (if it was previously `true`).

## Permissions
The request user needs:
- `motion.can_manage_polls` if the poll's content object is a motion
- `assignment.can_manage` if the poll's content object is an assignment
- `poll.can_manage` if the poll's content object is a topic
