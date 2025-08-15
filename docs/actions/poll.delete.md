## Payload
```js
{ id: Id; }
```

## Action
Deletes the given poll and all linked options with all votes, too.

## Permissions
The request user needs:
- `motion.can_manage_polls` if the poll's content object is a motion
- `assignment.can_manage_polls` if the poll's content object is an assignment
- `poll.can_manage` if the poll's content object is a topic
