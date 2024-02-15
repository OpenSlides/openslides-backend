# Payload
```
{
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
Go thru the database.
Run the checker.
If okay, it returns `{"ok": True}` else it returns `{"ok": False, "errors": <errors>}`.

# Permissions
The user must be OML Superadmin. 