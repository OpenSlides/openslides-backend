## Payload
```js
{id: Id;}
```

## Action
Only for non-analog polls in the state *finished* or *published*. Sets all `vote/user_id` and `vote/delegated_user_id` references to `None` for each vote of each option of the poll (including the global option).

`is_pseudoanonymized` has to be set to `true`.

## Permissions
The request user needs:
- `motion.can_manage_polls` if the poll's content object is a motion
- `assignment.can_manage_polls` if the poll's content object is an assignment
- `poll.can_manage` if the poll's content object is a topic
