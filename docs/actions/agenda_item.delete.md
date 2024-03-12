## Payload:
```
{ id: Id }
```

## Action
If the content object is a topic it has to be deleted, too. Else only the agenda item is deleted. All children of the agenda item have no parent anymore so they are moved into the root of the agenda.

## Permissions
The request user needs `agenda_item.can_manage`.
