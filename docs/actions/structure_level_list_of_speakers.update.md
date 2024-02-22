## Payload


```js
{
    id: Id;  // required
    initial_time: int;
    current_start_time: int | null;
    spoken_time: int;
}
```

## Action

If `initial_time` is changed, `remaining_time` will be set to the same value

`spoken_time` and `current_start_time` can only be given if the action is executed internally.

`spoken_time` is substracted from `structure_level_list_of_speakers/remaining_time`.
