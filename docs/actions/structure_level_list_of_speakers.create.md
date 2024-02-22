## Payload

```js
{
    structure_level_id: Id;  // required
    list_of_speakers_id: Id;  // required
    initial_time: int;
}
```

## Action

This action creates a new `structure_level_list_of_speakers` model with the given data. It is only
allowed if `meeting/list_of_speakers_default_structure_level_time > 0`. If `initial_time` is not
given, `meeting/list_of_speakers_default_structure_level_time` is used instead.

`remaining_time` is automatically set to `initial_time`.

The combination of `(structure_level_id, list_of_speakers_id)` must be unique in the meeting.

## Permissions

The request user needs `list_of_speakers.can_manage`.