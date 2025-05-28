## Payload
```js
{
    ids: Id[];
    parent_id: Id | null;
    meeting_id: Id;
}
```

## Action
Sets the agenda item referenced by `parent_id` as the parent of the agenda items referenced by `ids`. If `parent_id` is null, the items are added to the root layer. The keys `weight` and `level` are adjusted, to assure the items are "sorted" under the parent. The children of the assigned agenda items are also adjusted.

The action will raise an error, if cycles would be formed.

## Permissions
The request user needs `agenda_item.can_manage`.
