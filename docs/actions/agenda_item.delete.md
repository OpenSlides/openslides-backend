## Payload:
```js
{ id: Id }
```

## Action
If the content object is a topic, that topic is also deleted. Else, only the agenda item is deleted. All children of the agenda item no longer have a parent, so they are moved to the root of the agenda.

## Permissions
The request user needs `agenda_item.can_manage`.
