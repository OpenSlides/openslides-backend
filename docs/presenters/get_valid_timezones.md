# Payload
```js
{
}
```

# Returns
```js
{
    [string]: string
    ...
}
```

# Logic
Gets all valid timezones from database.

Returns a timezone-name to current abbreviation dict.
(Note: Abbreviations may change over the course of the year as certain timezones switch to and from DST)

In general this is going to return mostly canonic IANA timezone names.

# Permissions
The user must be OML Superadmin. 