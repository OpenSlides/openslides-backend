## Payload
```js
{
// Required
  content_object_id: Fqid

// Optional
  item_number: string;
  parent_id: Id;
  comment: string;
  type: number;
  duration: number; // in seconds
  weight: number;
  tag_ids: Id[];
}
```

## Action
Creates an agenda item for the content object. It fails, if the content object already has an agenda
item or the content object cannot have an agenda item (see available collections in the
`models.yml`). `tag_ids` must be from the same meeting.

## Permissions
The request user needs `agenda_item.can_manage`.
