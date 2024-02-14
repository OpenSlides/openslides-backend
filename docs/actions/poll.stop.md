## Payload
```
{id: Id;}
```

## Action
Sets the state to *finished*. Only allowed for polls in the *started* state.

If `meeting/poll_couple_countdown` is true, the countdown given by `meeting/poll_countdown_id` must be *reset* (see [[https://github.com/OpenSlides/OpenSlides/wiki/Countdowns#reset-a-countdown]]).

Some fields have to be calculated upon stopping a poll:
- The fields `votescast`, `votesvalid` and `votesinvalid` have to be filled (see [poll results](https://github.com/OpenSlides/OpenSlides/wiki/Voting#poll-results)). They are only filled once when the poll stops to prevent any changes e.g. from deleting users.
- `entitled_users_at_stop` has to be filled. It is an array of objects which represents all users entitled to vote at the stopping point of the poll. The syntax is `{"user_id": Id, "voted": boolean, "vote_delegated_to_id": Id | null}`. The fields should be self-explanatory. This field is also a snapshot like the ones above.

## Permissions
The request user needs:
- `motion.can_manage_polls` if the poll's content object is a motion
- `assignment.can_manage` if the poll's content object is an assignment
- `poll.can_manage` else
