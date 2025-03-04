## Payload
A helper-interface:
```
Interface TreeIdNode {
    id: Id;
    children?: TreeIdNode[];
}
```

Payload
```
{
    meeting_id: Id;
    tree: TreeIdNode[]; // recursive tree of ids.
}
```

## Action
Sorts the agenda items with the `agenda_item/parent_id` and `agenda_item/weight` fields.
Raises an error if the given tree doesn't include all items in `meeting/agenda_item_ids`.


## Permissions
The request user needs `agenda_item.can_manage`.
