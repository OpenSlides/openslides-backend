## Payload
```
{
    id: Id;
    motion_ids: Id[]
}
```

## Action
All `motion_ids` of this category must be given in the new order. The `motion/category_weight` is changed accordingly.

## Permissions
The request user needs `motion.can_manage`.
