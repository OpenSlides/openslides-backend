## Payload
```js
{
// required
    id: Id;

// Optional
    title: string;
    text: HTML;

    attachment_mediafile_ids: Ids[];
}
```

## Action
`attachment_mediafile_ids` must be from the same meeting or the mediafile must be published.

## Permissions
The request user needs `agenda_item.can_manage`.
