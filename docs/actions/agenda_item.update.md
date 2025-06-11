## Payload
```js
{
// Required
    id: Id;

// Optional
    item_number: string;
    comment: string;
    closed: boolean;
    type: string;
    duration: number; // in minutes
    weight: number;
    tag_ids: Id[];
}
```

## Action
Updates the agenda item. `tag_ids` must be from the same meeting.
The `type` attribute of one `agenda_item` must be one of [`common`, `internal`, `hidden`].

## Permissions
The request user needs `agenda_item.can_manage`.

