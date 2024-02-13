### Includes changes of feature branch `los-extension`!

## Payload

```js
{
    name: string; // required
    color: color;
    default_time: number;
}
```

## Action

This action creates a new structure level with the given name and adds it to the collection of `structure_level_ids` in a meeting given by the `meeting_id`.

The `name` must be unique in the meeting.

## Permissions

The request user needs `user.can_manage`.