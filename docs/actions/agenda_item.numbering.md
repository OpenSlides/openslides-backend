## Payload
```js
{meeting_id: Id}
```

## Action
Numbers all agenda items of the given meeting, writing the numbers into the `item_number` field.

For each agenda item creates a number in the format `<meeting/agenda_number_prefix> <number>` where `number` is determined as follows:
- If `meeting/agenda_numeral_system` is `arabic` (or empty), they are given arabic numbers according to their position by order, with child items being named by the schema `<parent number>.<position among children>`.
- If `meeting/agenda_numeral_system` is `roman`, the root items are given roman numbers by order, with child items expanding upon these numbers with arabic numerals, same as with the arabic system.

## Permissions
The request user needs `agenda_item.can_manage`.
