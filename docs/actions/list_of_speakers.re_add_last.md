## Payload
```
{ id: Id; }
```

## Action
Readds the last finished speaker user (the highest `end_time`) to the list of waiting speakers. This fails, if
- There is no last finished speaker
- The last finished speaker is already a waiting speaker with the same point-of-order status
- The speech state of the last speaker is `interposed_question` and there is no unfinished speaker

The new waiting speaker gets the weight of `min-1` of all waiting speakers or 1, if there are no waiting speakers.

## Permissions
The request user needs `list_of_speakers.can_manage`.
