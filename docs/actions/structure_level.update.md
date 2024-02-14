### Includes changes of feature branch `los-extension`!

## Payload

```js
{
    id: Id;  // required
    name: string;
    color: color;
    default_time: number;
}
```

## Action

This action updates a structure level given by the `id`.

The `name` must be unique in the meeting.

## Permission

The request user needs `user.can_manage`.
