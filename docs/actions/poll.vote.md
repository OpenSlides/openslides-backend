## Payload
```
{
    id: Id;  // poll.id to vote for
    user_id: id;  // in case of vote delegation the user to vote for

// pollmethod in (Y, N)
    value: {<option_id>: <amount>} | 'Y' | 'N' | 'A';

// pollmethod not in (Y, N)
    value: {<option_id>: 'Y' | 'N' | 'A'} | 'Y' | 'N' | 'A';
}
```

## Action
This action is not allowed for analog polls, use [option.update](option.update) to manipulate vote data per option.

 - Exactly one of the four options must be given (the object or `Y`/`N`/`A`)
 - 'Y' is only valid if `poll/global_yes` is true
 - 'N' is only valid if `poll/global_no` is true
 - 'A' is only valid if `poll/global_abstain` is true
 - `<option_id>` must be integers of valid option ids for this poll, but not the global option

Notes for pollmethod in (Y, N):
 - amounts must be integer numbers >= 0 and <= `poll/max_votes_per_option`.
 - The sum of all amounts must be >= `poll/min_votes_amount` and <= `poll/max_votes_amount`

For more details, see [Casting a ballot](https://github.com/OpenSlides/OpenSlides/wiki/Voting#cast-a-ballot).

## Permissions
See [User in vote objects](https://github.com/OpenSlides/OpenSlides/wiki/Voting#user-in-vote-objects) especially for the definition of _entitled users_ and the vote delegation feature.
