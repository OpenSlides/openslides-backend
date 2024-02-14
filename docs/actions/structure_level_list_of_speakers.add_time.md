### Includes changes of feature branch `los-extension`!

## Payload

```js
{
    id: Id;  // required
}
```

## Action

Increase the time of all structure levels by increasing
`additional_time` as well as `remaining_time` by the amount that the given structure level is
negative. It is only allowed if the given structure level is not currently active, i.e.,
`current_start_time` must be `None`, and if `meeting/list_of_speakers_default_structure_level_time > 0`.

Example: A speaker for structure level 1 spoke too long and the remaining time for it is -60 (60 seconds over its total time). The execution of `structure_level_list_of_speakers.add_time` with the id 1 now adds these 60 seconds to all structure levels, including structure level 1. Afterwards, structure level 1 is at remaining time 0 and all other structure levels have an additional minute of time.

## Permissions

The request user needs `list_of_speakers.can_manage`.