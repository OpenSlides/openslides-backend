## Payload
A helper-interface:
```js
Interface TreeIdNode {
    id: Id;
    // Optional
    children: TreeIdNode[];
}
```

Payload:
```js
{
    meeting_id: Id;
    tree: TreeIdNode[]; // recursive tree of ids.
}
```

## Action
Sorts all motions of the meeting in a tree by `motion/sort_parent_id` and `motion/sort_weight`. All motion ids of the meeting must be given.

## Permissions
The request user needs `motion.can_manage`.
