## Payload
```
{
// Required
    id: Id;

// Optional
    name: string;
    read_group_ids: Id[];
    write_group_ids: Id[];
    submitter_can_write: boolean;
}
```


## Action
Updates the comment section. The given groups must belong to the same meeting.

## Permissions
The request user needs `motion.can_manage`.
