## Payload

A helper-interface:
```
Interface TreeIdNode {
    id: Id;
    children?: TreeIdNode[];
}
```

Actual payload:
```
{
    meeting_id: Id;
    tree: TreeIdNode[]; // recursive tree of ids.
}
```

## Action
All category ids of th meeting must be given. Sorts the categories with the `motion_category/parent_id` and `motion_category/weight` fields.

## Permissions
The request user needs `motion.can_manage`.
