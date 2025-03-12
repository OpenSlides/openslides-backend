# Payload
```js
{
    // optional
    meeting_id: integer
}
```

# Returns
If okay:
```js
{
    ok: boolean
}
```
else:
```js
{
    ok: boolean,
    errors: string
}
```

# Logic
Runs the checker.
Goes through all meetings. If `meeting_id` is given, it will check just this meeting.
If okay, it returns `{"ok": True}` else it returns `{"ok": False, "errors": <errors>}`.

# Permissions
The user must be OML Superadmin. 