# Payload

```
{
    meeting_id: Id
}
```

# Returns

```
string[]
```

# Logic

If the user does not have `motion.can_manage_metadata` in the given meeting, an error is thrown. 

The relation `meeting/committee_id` -> `committee/receive_forwardings_from_committee_ids` is followed.
The names of all meetings in the forwarding committees are collected in a list, which is then returned.
