# Payload

```js
{
    meeting_id: Id // required
    for_agenda: boolean // optional
}
```

# Returns

```js
[
    {
        id: Id,
        name: string,
        default_meeting_id: Id,
        meeting: [{id: Id, name: string, start_time:timestamp|null, end_time:timestamp|null}, ...]
    },
    ...
]
```
or `{ok: False}` on errors

# Logic

If the user does not have `motion.can_forward` in the given meeting, an error is returned. 
If the given meeting is archived or there is no committee, an exception is thrown and an error is returned.

The relation `meeting/committee_id` -> `committee/forward_to_committee_ids` is followed. A list is returned. Every committee in the list generates one entry:

For each meeting in the committee it is checked whether it is active (`is_active_in_organization_id`). All those meetings are collected in a list represented by `{id: <meeting/id>, name: <meeting/name>}`. For the committee, this object is created:
```
{
    id: <committee/id>,
    name: <committee/name>,
    default_meeting_id: <committee/default_meeting_id>
    meetings: <List of meetings>
}
```
A list of these objects is returned to the caller.
