# Payload

```js
{
    fqid: Fqid // required
}
```

## Returns

```js
{
    information: {[fqid]: string[]}
    position: int;
    user: string; // username of user
    timestamp: number;
}[]
```

## Logic

Return all history information for one fqid.

## Permissions

Requester needs to have oml superadmin.