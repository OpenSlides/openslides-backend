## Payload
```js
{
    // required
    text: string;
    rank: integer;
    meeting_id: Id;
}
```

## Action
Creates a `point_of_order_category` for the meeting `meeting_id`.

## Permissions
The user needs to have the `meeting.can_manage_settings` of the meeting.