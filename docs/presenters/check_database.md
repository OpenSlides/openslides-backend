# Payload
```
{
    // optional
    meeting_id: integer;
}
```

# Returns
If okay:
```
{
    ok: boolean,
}
```
else:
```
{
    ok: boolean,
    errors: string,
}
```

# Logic
Go thru all meetings. If `meeting_id` is given, it just will check this meeting. Run the checker.
If okay, it returns `{"ok": True}` else it returns `{"ok": False, "errors": <errors>}`.

# Permissions
The user must be OML Superadmin. 