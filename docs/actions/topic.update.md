## Payload
```
{
// required
    id: Id;

// Optional
    title: string;
    text: HTML;

    attachment_ids: Ids[];
    tag_ids: Ids[];
}
```

## Action
`attachment_ids` and `tag_ids` must be from the same meeting.

## Permissions
The request user needs `agenda_item.can_manage`.
