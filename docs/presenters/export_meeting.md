# Payload

```
{
    meeting_id: Id
}
```

# Returns

```
JSON with export
```

# Logic
The presenter exports the meeting, the collections which belong to the meeting and users of the meeting. It uses the meeting.user_id for that. And it excludes the organization tags and the committee.
Will raise an exception if the meeting is locked voa the `locked_from_inside` setting.

# Permissions
The request user must have the `SUPERADMIN` organization management level.


