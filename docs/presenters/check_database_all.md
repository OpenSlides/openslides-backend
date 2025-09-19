# Payload
```js
{
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
Goes through the database.
If okay, it returns `{"ok": True}` else it returns `{"ok": False, "errors": <errors>}`.

# Permissions
The user must be OML Superadmin. 