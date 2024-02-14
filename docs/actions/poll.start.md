## Payload
```
{id: Id;}
```

## Action
Sets the state to *started*. Only allowed for polls in the *created* state.

If `meeting/poll_couple_countdown` is true and the poll is an electronic poll, the countdown given by `meeting/poll_countdown_id` must be *restarted* (see [[https://github.com/OpenSlides/OpenSlides/wiki/Countdowns#restart-a-countdown]]).

## Permissions
The request user needs:
- `motion.can_manage_polls` if the poll's content object is a motion
- `assignment.can_manage` if the poll's content object is an assignment
- `poll.can_manage` else
